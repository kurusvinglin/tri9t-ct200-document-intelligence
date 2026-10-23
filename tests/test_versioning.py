
from app.versioning import (
    normalize_text,
    calculate_content_hash,
    has_content_changed,
)


def test_whitespace_does_not_change_hash():
    assert calculate_content_hash("Keep it dry.") == calculate_content_hash(
        "  Keep   it dry.  "
    )


def test_changed_text_has_different_hash():
    assert calculate_content_hash("Keep it dry.") != calculate_content_hash(
        "Keep it clean and dry."
    )


def test_has_content_changed():
    assert has_content_changed("Use the monitor.", "Use the monitor.") is False
    assert has_content_changed("Use the monitor.", "Do not use the monitor.") is True


def test_normalize_text():
    assert normalize_text("  Keep \n the   monitor dry. ") == "Keep the monitor dry."
