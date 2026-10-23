
import pytest

from app.generation import (
    QAGenerationResult,
    generate_qa_tests,
)


def test_empty_text_is_rejected():
    with pytest.raises(ValueError, match="Section text cannot be empty"):
        generate_qa_tests("")


def test_whitespace_text_is_rejected():
    with pytest.raises(ValueError, match="Section text cannot be empty"):
        generate_qa_tests("   \n  ")


def test_generator_returns_three_to_five_valid_tests():
    result = generate_qa_tests(
        "Keep the blood pressure monitor dry and use it according "
        "to the instructions."
    )

    assert isinstance(result, QAGenerationResult)
    assert 3 <= len(result.tests) <= 5

    for test in result.tests:
        assert test.title.strip()
        assert len(test.steps) >= 1
        assert test.expected_result.strip()


def test_generated_steps_reference_selected_text():
    result = generate_qa_tests("Keep the monitor dry.")

    assert "Keep the monitor dry." in result.tests[0].steps[0]
