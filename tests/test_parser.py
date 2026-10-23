
from app.parser import extract_pdf_text, extract_sections


def test_extract_pdf_text():
    pages = extract_pdf_text("data/ct200_manual.pdf")

    assert len(pages) > 0
    assert "page_number" in pages[0]
    assert "text" in pages[0]


def test_duplicate_headings_are_preserved():
    pages = [{
        "page_number": 1,
        "text": "1 Safety\nWear the cuff correctly.\n2 Safety\nKeep the monitor dry."
    }]

    sections = extract_sections(pages)
    safety_sections = [
        section for section in sections
        if section["heading"] == "1 Safety"
        or section["heading"] == "2 Safety"
    ]

    assert len(safety_sections) == 2


def test_numbered_heading_parent():
    pages = [{
        "page_number": 1,
        "text": (
            "1 Instructions\nGeneral instructions.\n"
            "1.1 Setup\nPlace the monitor on a table.\n"
            "1.1.1 Power\nInsert the batteries."
        )
    }]

    sections = extract_sections(pages)
    by_heading = {section["heading"]: section for section in sections}

    assert by_heading["1.1 Setup"]["parent_heading"] == "1 Instructions"
    assert by_heading["1.1.1 Power"]["parent_heading"] == "1.1 Setup"


def test_body_text_is_preserved():
    pages = [{
        "page_number": 1,
        "text": "1 Safety\nDo not immerse the monitor in water."
    }]

    sections = extract_sections(pages)

    assert any(
        "Do not immerse the monitor in water."
        in section["body_text"]
        for section in sections
    )

def test_duplicate_headings_under_different_parents():
    pages = [{
        "page_number": 1,
        "text": (
            "1 Setup\n"
            "1.1 General\n"
            "Instructions for setup.\n"
            "2 Maintenance\n"
            "2.1 General\n"
            "Instructions for maintenance."
        )
    }]

    sections = extract_sections(pages)
    general_sections = [
        section for section in sections
        if section["heading"].endswith("General")
    ]

    assert len(general_sections) == 2
    assert general_sections[0]["parent_heading"] == "1 Setup"
    assert general_sections[1]["parent_heading"] == "2 Maintenance"
