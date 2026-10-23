
import pymupdf
import re

from app.versioning import calculate_content_hash


def extract_pdf_text(pdf_path: str) -> list[dict]:
    pages = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            pages.append({
                "page_number": page_number,
                "text": page.get_text("text")
            })

    return pages


def extract_sections(pages: list[dict]) -> list[dict]:
    sections = []
    current = None

    for page in pages:
        for line in page["text"].splitlines():
            line = line.strip()

            if not line:
                continue

            match = re.match(r"^(\d+(?:\.\d+)*)\s+(.+)$", line)

            is_heading = (
                match is not None
                or (
                    len(line) < 100
                    and len(line.split()) <= 8
                    and line.isupper()
                )
            )

            if is_heading:
                if current:
                    current["body_text"] = "\n".join(current.pop("_lines"))
                    current["content_hash"] = calculate_content_hash(
                        current["body_text"]
                    )
                    sections.append(current)

                if match:
                    number = match.group(1)
                    heading = line
                    level = number.count(".") + 1
                else:
                    number = None
                    heading = line
                    level = 1

                current = {
                    "heading": heading,
                    "level": level,
                    "parent_heading": None,
                    "body_text": "",
                    "content_hash": "",
                    "_number": number,
                    "_lines": []
                }

            else:
                if current is None:
                    current = {
                        "heading": "Introduction",
                        "level": 1,
                        "parent_heading": None,
                        "body_text": "",
                        "content_hash": "",
                        "_number": None,
                        "_lines": []
                    }

                current["_lines"].append(line)

    if current:
        current["body_text"] = "\n".join(current.pop("_lines"))
        current["content_hash"] = calculate_content_hash(
            current["body_text"]
        )
        sections.append(current)

    # Identify parent headings for numbered sections.
    stack = []

    for section in sections:
        number = section["_number"]

        if number:
            level = section["level"]

            while stack and stack[-1]["level"] >= level:
                stack.pop()

            if stack:
                section["parent_heading"] = stack[-1]["heading"]

            stack.append({
                "heading": section["heading"],
                "level": level
            })

        else:
            section["parent_heading"] = None

    # Remove internal parsing metadata.
    for section in sections:
        section.pop("_number", None)

    return sections
