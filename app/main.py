import json
from app.models import DocumentVersion, DocumentNode, NamedSelection
import json
from app.models import DocumentVersion, DocumentNode, NamedSelection, GeneratedQA
from app.generation import generate_qa_tests 

import json
from pydantic import BaseModel

from pathlib import Path

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models import DocumentVersion, DocumentNode
from app.parser import extract_pdf_text, extract_sections

app = FastAPI(title="Tri9T CT-200 Document Intelligence API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "CT-200 Document Intelligence API is running"}


@app.post("/ingest/{version_name}")
def ingest_document(version_name: str, filename: str):
    pdf_path = Path("data") / filename

    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF file not found")

    db: Session = SessionLocal()

    try:
        existing = (
            db.query(DocumentVersion)
            .filter_by(version_name=version_name)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="This version already exists"
            )

        pages = extract_pdf_text(str(pdf_path))
        sections = extract_sections(pages)

        if not sections:
            raise HTTPException(
                status_code=422,
                detail="No sections could be extracted from the PDF"
            )

        version = DocumentVersion(
            version_name=version_name,
            filename=filename
        )
        db.add(version)
        db.flush()

        
        created_nodes = []
        pending_sections = []

        for section in sections:
            node = DocumentNode(
                version_id=version.id,
                heading=section["heading"],
                level=section["level"],
                body_text=section["body_text"],
                content_hash=section["content_hash"]
            )
            db.add(node)
            created_nodes.append(node)
            pending_sections.append(section)

        db.flush()

        for node, section in zip(created_nodes, pending_sections):
            parent_heading = section.get("parent_heading")

            if parent_heading:
                parent = next(
                    (
                        candidate
                        for candidate in created_nodes
                        if candidate.heading == parent_heading
                    ),
                    None
                )

                if parent:
                    node.parent_id = parent.id

        db.commit()


        db.commit()

        return {
            "message": "Document ingested successfully",
            "version": version_name,
            "pages": len(pages),
            "sections": len(sections)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()
        
        
@app.get("/compare/{old_version}/{new_version}")
def compare_versions(old_version: str, new_version: str):
    db = SessionLocal()

    try:
        old = (
            db.query(DocumentVersion)
            .filter_by(version_name=old_version)
            .first()
        )
        new = (
            db.query(DocumentVersion)
            .filter_by(version_name=new_version)
            .first()
        )

        if not old or not new:
            raise HTTPException(
                status_code=404,
                detail="One or both document versions were not found"
            )

        old_nodes = db.query(DocumentNode).filter_by(
            version_id=old.id
        ).all()

        new_nodes = db.query(DocumentNode).filter_by(
            version_id=new.id
        ).all()

        # Compare sections by heading for this initial implementation.
        old_by_heading = {}
        new_by_heading = {}

        for node in old_nodes:
            old_by_heading.setdefault(node.heading, []).append(node)

        for node in new_nodes:
            new_by_heading.setdefault(node.heading, []).append(node)

        changes = []

        for heading in sorted(set(old_by_heading) | set(new_by_heading)):
            old_group = old_by_heading.get(heading, [])
            new_group = new_by_heading.get(heading, [])

            count = max(len(old_group), len(new_group))

            for i in range(count):
                old_node = old_group[i] if i < len(old_group) else None
                new_node = new_group[i] if i < len(new_group) else None

                if old_node and new_node:
                    if old_node.content_hash == new_node.content_hash:
                        status = "unchanged"
                    else:
                        status = "modified"
                elif old_node:
                    status = "removed"
                else:
                    status = "added"

                changes.append({
                    "heading": heading,
                    "old_node_id": old_node.id if old_node else None,
                    "new_node_id": new_node.id if new_node else None,
                    "status": status
                })

        return {
            "old_version": old_version,
            "new_version": new_version,
            "changes": changes
        }

    finally:
        db.close()
        
        
@app.get("/sections/{version_name}")
def list_sections(version_name: str):
    db = SessionLocal()

    try:
        version = (
            db.query(DocumentVersion)
            .filter_by(version_name=version_name)
            .first()
        )

        if not version:
            raise HTTPException(
                status_code=404,
                detail="Document version not found"
            )

        nodes = (
            db.query(DocumentNode)
            .filter_by(version_id=version.id)
            .order_by(DocumentNode.id)
            .all()
        )

        return {
            "version": version_name,
            "total_sections": len(nodes),
            "sections": [
                {
                    "id": node.id,
                    "heading": node.heading,
                    "level": node.level,
                    "body_text": node.body_text,
                    "content_hash": node.content_hash
                }
                for node in nodes
            ]
        }

    finally:
        db.close()


@app.get("/nodes/{node_id}")
def get_node(node_id: int):
    db = SessionLocal()

    try:
        node = db.query(DocumentNode).filter_by(id=node_id).first()

        if not node:
            raise HTTPException(
                status_code=404,
                detail="Section not found"
            )

        children = (
            db.query(DocumentNode)
            .filter_by(parent_id=node.id)
            .all()
        )

        return {
            "id": node.id,
            "version_id": node.version_id,
            "heading": node.heading,
            "level": node.level,
            "body_text": node.body_text,
            "content_hash": node.content_hash,
            "children": [
                {
                    "id": child.id,
                    "heading": child.heading,
                    "level": child.level
                }
                for child in children
            ]
        }

    finally:
        db.close()

@app.get("/search")
def search_sections(q: str, version_name: str = "v1"):
    db = SessionLocal()

    try:
        version = (
            db.query(DocumentVersion)
            .filter_by(version_name=version_name)
            .first()
        )

        if not version:
            raise HTTPException(
                status_code=404,
                detail="Document version not found"
            )

        nodes = (
            db.query(DocumentNode)
            .filter(
                DocumentNode.version_id == version.id,
                (
                    DocumentNode.heading.ilike(f"%{q}%")
                    | DocumentNode.body_text.ilike(f"%{q}%")
                )
            )
            .order_by(DocumentNode.id)
            .all()
        )

        return {
            "version": version_name,
            "query": q,
            "results_count": len(nodes),
            "results": [
                {
                    "id": node.id,
                    "heading": node.heading,
                    "level": node.level,
                    "body_text": node.body_text,
                    "content_hash": node.content_hash
                }
                for node in nodes
            ]
        }

    finally:
        db.close()



class SelectionRequest(BaseModel):
    name: str
    version_name: str
    node_ids: list[int]


@app.post("/selections")
def create_selection(request: SelectionRequest):
    db = SessionLocal()

    try:
        version = (
            db.query(DocumentVersion)
            .filter_by(version_name=request.version_name)
            .first()
        )

        if not version:
            raise HTTPException(
                status_code=404,
                detail="Document version not found"
            )

        if not request.node_ids:
            raise HTTPException(
                status_code=400,
                detail="Select at least one node"
            )

        nodes = (
            db.query(DocumentNode)
            .filter(
                DocumentNode.version_id == version.id,
                DocumentNode.id.in_(request.node_ids)
            )
            .all()
        )

        if len(nodes) != len(set(request.node_ids)):
            raise HTTPException(
                status_code=400,
                detail="One or more node IDs are invalid for this version"
            )

        if db.query(NamedSelection).filter_by(name=request.name).first():
            raise HTTPException(
                status_code=409,
                detail="Selection name already exists"
            )

        selection = NamedSelection(
            name=request.name,
            version_id=version.id,
            node_ids_json=json.dumps(request.node_ids)
        )

        db.add(selection)
        db.commit()
        db.refresh(selection)

        return {
            "selection_id": selection.id,
            "name": selection.name,
            "version": request.version_name,
            "node_ids": request.node_ids
        }

    finally:
        db.close()

@app.get("/selections/{selection_id}")
def get_selection(selection_id: int):
    db = SessionLocal()

    try:
        selection = (
            db.query(NamedSelection)
            .filter_by(id=selection_id)
            .first()
        )

        if not selection:
            raise HTTPException(
                status_code=404,
                detail="Selection not found"
            )

        node_ids = json.loads(selection.node_ids_json)

        nodes = (
            db.query(DocumentNode)
            .filter(
                DocumentNode.version_id == selection.version_id,
                DocumentNode.id.in_(node_ids)
            )
            .all()
        )

        return {
            "selection_id": selection.id,
            "name": selection.name,
            "version_id": selection.version_id,
            "nodes": [
                {
                    "id": node.id,
                    "heading": node.heading,
                    "body_text": node.body_text,
                    "content_hash": node.content_hash
                }
                for node in nodes
            ]
        }

    finally:
        db.close()

@app.post("/generate/{selection_id}")
def generate_tests_for_selection(selection_id: int):
    db = SessionLocal()

    try:
        selection = (
            db.query(NamedSelection)
            .filter_by(id=selection_id)
            .first()
        )

        if not selection:
            raise HTTPException(
                status_code=404,
                detail="Selection not found"
            )

        node_ids = json.loads(selection.node_ids_json)

        nodes = (
            db.query(DocumentNode)
            .filter(
                DocumentNode.version_id == selection.version_id,
                DocumentNode.id.in_(node_ids)
            )
            .all()
        )

        if not nodes:
            raise HTTPException(
                status_code=422,
                detail="Selection contains no available source nodes"
            )

        source_snapshot = [
            {
                "node_id": node.id,
                "heading": node.heading,
                "content_hash": node.content_hash,
                "body_text": node.body_text
            }
            for node in nodes
        ]

        section_text = "\n\n".join(
            f"{node.heading}\n{node.body_text}"
            for node in nodes
        )

        result = generate_qa_tests(section_text)

        record = GeneratedQA(
            selection_id=selection.id,
            source_snapshot_json=json.dumps(source_snapshot),
            generated_tests_json=result.model_dump_json()
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "generation_id": record.id,
            "selection_id": selection.id,
            "test_count": len(result.tests),
            "tests": result.model_dump()
        }

    finally:
        db.close()

@app.get("/generation/{generation_id}/staleness")
def check_generation_staleness(generation_id: int):
    db = SessionLocal()

    try:
        record = (
            db.query(GeneratedQA)
            .filter_by(id=generation_id)
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=404,
                detail="Generation record not found"
            )

        snapshot = json.loads(record.source_snapshot_json)
        selection = (
            db.query(NamedSelection)
            .filter_by(id=record.selection_id)
            .first()
        )

        if not selection:
            raise HTTPException(
                status_code=404,
                detail="Source selection not found"
            )

        stale_nodes = []

        for old_node in snapshot:
            current_node = (
                db.query(DocumentNode)
                .filter_by(
                    id=old_node["node_id"],
                    version_id=selection.version_id
                )
                .first()
            )

            if (
                current_node is None
                or current_node.content_hash != old_node["content_hash"]
            ):
                stale_nodes.append({
                    "node_id": old_node["node_id"],
                    "heading": old_node["heading"],
                    "status": "changed_or_missing"
                })

        return {
            "generation_id": generation_id,
            "selection_id": selection.id,
            "stale": bool(stale_nodes),
            "status": "stale" if stale_nodes else "current",
            "affected_nodes": stale_nodes,
            "limitation": (
                "Checks source-node hashes only; it does not determine "
                "whether wording changes affect the meaning of each QA test."
            )
        }

    finally:
        db.close()

@app.get("/generation/{generation_id}/staleness/{current_version}")
def check_staleness_against_version(
    generation_id: int,
    current_version: str
):
    db = SessionLocal()

    try:
        record = db.query(GeneratedQA).filter_by(
            id=generation_id
        ).first()

        if not record:
            raise HTTPException(
                status_code=404,
                detail="Generation record not found"
            )

        new_version = db.query(DocumentVersion).filter_by(
            version_name=current_version
        ).first()

        if not new_version:
            raise HTTPException(
                status_code=404,
                detail="Current document version not found"
            )

        snapshot = json.loads(record.source_snapshot_json)
        affected_nodes = []

        for old_node in snapshot:
            old_heading = old_node["heading"]

            candidates = db.query(DocumentNode).filter_by(
                version_id=new_version.id,
                heading=old_heading
            ).all()

            match = next(
                (
                    node for node in candidates
                    if node.content_hash == old_node["content_hash"]
                ),
                None
            )

            if match:
                status = "unchanged"
            elif candidates:
                status = "modified_or_ambiguous"
            else:
                status = "missing"

            if status != "unchanged":
                affected_nodes.append({
                    "original_node_id": old_node["node_id"],
                    "heading": old_heading,
                    "status": status
                })

        return {
            "generation_id": generation_id,
            "compared_version": current_version,
            "stale": bool(affected_nodes),
            "status": "stale" if affected_nodes else "current",
            "affected_nodes": affected_nodes,
            "limitation": (
                "Matching uses heading and content hash. Duplicate headings "
                "may be ambiguous, and semantic impact is not evaluated."
            )
        }

    finally:
        db.close()

@app.get("/sections/{version_name}/top-level")
def get_top_level_sections(version_name: str):
    db = SessionLocal()
    try:
        version = (
            db.query(DocumentVersion)
            .filter_by(version_name=version_name)
            .first()
        )

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Document version not found"
            )

        sections = (
            db.query(DocumentNode)
            .filter(
                DocumentNode.version_id == version.id,
                DocumentNode.parent_id.is_(None)
            )
            .order_by(DocumentNode.id)
            .all()
        )

        return {
            "version": version_name,
            "count": len(sections),
            "sections": [
                {
                    "id": section.id,
                    "heading": section.heading,
                    "level": section.level,
                    "content_hash": section.content_hash
                }
                for section in sections
            ]
        }
    finally:
        db.close()
