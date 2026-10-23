
import hashlib
import re


def normalize_text(text: str) -> str:
    """Normalize whitespace before comparing section text."""
    return re.sub(r"\s+", " ", text).strip()


def calculate_content_hash(text: str) -> str:
    """Generate a SHA-256 hash for normalized text."""
    normalized = normalize_text(text)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def has_content_changed(old_text: str, new_text: str) -> bool:
    """Return True if the meaningful text content differs."""
    return calculate_content_hash(old_text) != calculate_content_hash(new_text)
