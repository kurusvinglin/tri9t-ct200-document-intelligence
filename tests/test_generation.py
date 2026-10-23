
import pytest
import app.generation as generation
from app.generation import QAGenerationResult, QATestIdea, generate_qa_tests


def make_valid_result():
    return QAGenerationResult(
        tests=[
            QATestIdea(
                title="Verify monitor is kept dry",
                steps=["Review the manual instruction"],
                expected_result="The documented instruction is followed.",
            ),
            QATestIdea(
                title="Verify operating instructions",
                steps=["Follow the documented procedure"],
                expected_result="The procedure matches the manual.",
            ),
            QATestIdea(
                title="Verify expected behavior",
                steps=["Check the documented device behavior"],
                expected_result="Behavior is consistent with the manual.",
            ),
        ]
    )


class FakeResponses:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.last_input = None

    def parse(self, **kwargs):
        self.calls += 1
        self.last_input = kwargs["input"]
        return type("FakeResponse", (), {
            "output_parsed": self.result
        })()


class FakeClient:
    def __init__(self, result, **kwargs):
        self.responses = FakeResponses(result)


def test_empty_text_is_rejected():
    with pytest.raises(ValueError, match="Section text cannot be empty"):
        generate_qa_tests("")


def test_whitespace_text_is_rejected():
    with pytest.raises(ValueError, match="Section text cannot be empty"):
        generate_qa_tests("   \n  ")


def test_generator_returns_three_to_five_valid_tests(monkeypatch):
    fake_client = FakeClient(make_valid_result())
    monkeypatch.setattr(generation, "OpenAI", lambda **kwargs: fake_client)
    monkeypatch.setattr(generation.time, "sleep", lambda _: None)
    monkeypatch.setattr(generation, "load_dotenv", lambda: None)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = generate_qa_tests(
        "Keep the blood pressure monitor dry and use it according "
        "to the instructions."
    )

    assert isinstance(result, QAGenerationResult)
    assert 3 <= len(result.tests) <= 5
    assert fake_client.responses.calls == 1


def test_generated_request_includes_selected_text(monkeypatch):
    fake_client = FakeClient(make_valid_result())
    monkeypatch.setattr(generation, "OpenAI", lambda **kwargs: fake_client)
    monkeypatch.setattr(generation.time, "sleep", lambda _: None)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    generate_qa_tests("Keep the monitor dry.")

    assert "Keep the monitor dry." in (
        fake_client.responses.last_input[1]["content"]
    )


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        generate_qa_tests("Keep the monitor dry.")
def test_generator_retries_when_response_is_invalid(monkeypatch):
    valid_result = make_valid_result()

    class RetryResponses:
        def __init__(self):
            self.calls = 0

        def parse(self, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return type("FakeResponse", (), {
                    "output_parsed": None
                })()

            return type("FakeResponse", (), {
                "output_parsed": valid_result
            })()

    fake_responses = RetryResponses()

    class RetryClient:
        def __init__(self, **kwargs):
            self.responses = fake_responses

    monkeypatch.setattr(generation, "OpenAI", RetryClient)
    monkeypatch.setattr(generation.time, "sleep", lambda _: None)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = generate_qa_tests("Keep the monitor dry.")

    assert len(result.tests) == 3
    assert fake_responses.calls == 2

        
        
