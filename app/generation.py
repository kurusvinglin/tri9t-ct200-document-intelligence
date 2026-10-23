from openai import (
    OpenAI,
    APIError,
    RateLimitError,
    APIConnectionError,
    AuthenticationError,
)


import os
import time

from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError
from pydantic import BaseModel, Field, ValidationError


load_dotenv()

MAX_ATTEMPTS = 3


class QATestIdea(BaseModel):
    title: str = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)


class QAGenerationResult(BaseModel):
    tests: list[QATestIdea] = Field(min_length=3, max_length=5)


def generate_qa_tests(section_text: str) -> QAGenerationResult:
    """Generate and validate QA tests using a real OpenAI model."""

    if not section_text or not section_text.strip():
        raise ValueError("Section text cannot be empty")

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(
        api_key=api_key,
        max_retries=0,
        timeout=30.0,
    )

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.responses.parse(
                model=model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a software QA engineer. Generate "
                            "3 to 5 practical test ideas based ONLY on "
                            "the supplied manual text. Do not invent "
                            "device specifications or safety thresholds. "
                            "Each test must have a title, steps, and "
                            "expected_result. If the text does not support "
                            "a detail, state that it needs verification."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Create QA test ideas from this manual excerpt:\n\n"
                            + section_text[:12000]
                        ),
                    },
                ],
                text_format=QAGenerationResult,
            )

            result = response.output_parsed

            if result is None:
                raise ValueError(
                    "The model returned no parsed structured output"
                )

            # Validate once more before returning.
            return QAGenerationResult.model_validate(
                result.model_dump()
            )

        
        except AuthenticationError as exc:
            raise RuntimeError(
                "OpenAI authentication failed. Check your API key "
                "in the .env file."
            ) from exc

        except (ValidationError, ValueError) as exc:
            last_error = exc

        except (RateLimitError, APIConnectionError, APIError) as exc:
            last_error = exc

        if attempt < MAX_ATTEMPTS:
            time.sleep(attempt)


    raise RuntimeError(
        f"QA generation failed after {MAX_ATTEMPTS} attempts: "
        f"{type(last_error).__name__}: {last_error}"
    ) from last_error
