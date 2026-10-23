
from pydantic import BaseModel, Field


class QATestIdea(BaseModel):
    title: str
    steps: list[str] = Field(min_length=1)
    expected_result: str


class QAGenerationResult(BaseModel):
    tests: list[QATestIdea] = Field(min_length=3, max_length=5)


def generate_qa_tests(section_text: str) -> QAGenerationResult:
    """Generate placeholder QA tests from selected manual text."""
    if not section_text.strip():
        raise ValueError("Section text cannot be empty")

    result = QAGenerationResult(
        tests=[
            QATestIdea(
                title="Verify documented instructions",
                steps=[
                    "Read the selected manual instructions",
                    "Follow the documented procedure"
                ],
                expected_result=(
                    "The procedure follows the supplied manual instructions."
                )
            ),
            QATestIdea(
                title="Verify safety information",
                steps=[
                    "Identify the safety precautions in the selected text",
                    "Check that the precautions are followed"
                ],
                expected_result=(
                    "The documented safety precautions are followed."
                )
            ),
            QATestIdea(
                title="Verify expected device behavior",
                steps=[
                    "Identify the behavior described in the selected text",
                    "Check the device against that description"
                ],
                expected_result=(
                    "The observed behavior matches the supplied instructions."
                )
            )
        ]
    )

    return result
