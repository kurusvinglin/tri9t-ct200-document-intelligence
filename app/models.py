
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String, nullable=False, unique=True)
    filename = Column(String, nullable=False)

    nodes = relationship(
        "DocumentNode",
        back_populates="version",
        cascade="all, delete-orphan"
    )


class DocumentNode(Base):
    __tablename__ = "document_nodes"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(
        Integer,
        ForeignKey("document_versions.id"),
        nullable=False
    )
    heading = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    body_text = Column(Text, default="")
    parent_id = Column(Integer, ForeignKey("document_nodes.id"), nullable=True)
    content_hash = Column(String, nullable=False)

    version = relationship("DocumentVersion", back_populates="nodes")

    children = relationship(
        "DocumentNode",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    parent = relationship(
        "DocumentNode",
        back_populates="children",
        remote_side=[id]
    )

class NamedSelection(Base):
    __tablename__ = "named_selections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    version_id = Column(
        Integer,
        ForeignKey("document_versions.id"),
        nullable=False
    )
    node_ids_json = Column(Text, nullable=False)
    
class GeneratedQA(Base):
    __tablename__ = "generated_qa"

    id = Column(Integer, primary_key=True, index=True)
    selection_id = Column(
        Integer,
        ForeignKey("named_selections.id"),
        nullable=False
    )
    source_snapshot_json = Column(Text, nullable=False)
    generated_tests_json = Column(Text, nullable=False)

