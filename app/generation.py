
from pydantic import BaseModel, Field, ValidationError


class QATestIdea(BaseModel):
    title: str = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)


class QAGenerationResult(BaseModel):
    tests: list[QATestIdea] = Field(min_length=3, max_length=5)


def generate_qa_tests(section_text: str) -> QAGenerationResult:
    """
    Generate placeholder QA tests.

    IMPORTANT:
    This is a deterministic mock generator, not a live LLM.
    The assignment's real LLM integration remains a limitation.
    """
    if not section_text or not section_text.strip():
        raise ValueError("Section text cannot be empty")

    # Use the selected manual text as the subject of the examples.
    excerpt = " ".join(section_text.split())[:160]

    result = QAGenerationResult(
        tests=[
            QATestIdea(
                title="Verify documented instructions",
                steps=[
                    f"Review this selected manual text: {excerpt}",
                    "Follow the applicable documented procedure"
                ],
                expected_result=(
                    "The procedure is consistent with the selected manual text."
                )
            ),
            QATestIdea(
                title="Verify safety information",
                steps=[
                    "Identify any safety precautions in the selected text",
                    "Check that the applicable precautions are followed"
                ],
                expected_result=(
                    "Applicable documented safety precautions are followed."
                )
            ),
            QATestIdea(
                title="Verify expected device behavior",
                steps=[
                    "Identify the device behavior described in the selected text",
                    "Compare the expected behavior with the documented instructions"
                ],
                expected_result=(
                    "The expected behavior is consistent with the selected text."
                )
            )
        ]
    )

    # Explicitly validate the final structured result.
    return QAGenerationResult.model_validate(result.model_dump())
