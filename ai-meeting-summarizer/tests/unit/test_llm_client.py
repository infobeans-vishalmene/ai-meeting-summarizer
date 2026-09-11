import pytest

from app.services.llm_client import summarize, LLMTimeoutError, LLMError


def test_summarize_parses_valid_response(mock_bedrock_success):
    result = summarize("some transcript text")
    assert result["key_points"] == ["Q4 targets on track"]
    assert result["action_items"][1]["owner"] == "unassigned"


def test_summarize_raises_timeout_on_read_timeout(mock_bedrock_timeout):
    with pytest.raises(LLMTimeoutError):
        summarize("some transcript text")


def test_summarize_raises_llm_error_on_missing_fields(mock_bedrock_malformed):
    # Bedrock returned valid JSON, but not with the required key_points/
    # decisions/action_items shape -- this is the "valid JSON, wrong shape"
    # gap flagged during the checklist discussion, not just "invalid JSON".
    with pytest.raises(LLMError, match="missing required fields"):
        summarize("some transcript text")


def test_summarize_strips_markdown_fence_before_parsing(monkeypatch):
    """
    Regression test for a real failure hit against live Bedrock: Nova Lite
    wrapped its JSON output in ```json ... ``` fences despite the prompt
    explicitly saying not to. This caused json.loads() to fail with
    "Expecting value: line 1 column 1 (char 0)" on the literal backtick.
    """
    import json as json_module
    from io import BytesIO
    from unittest.mock import MagicMock, patch

    fenced_text = (
        '```json\n{"key_points": ["a"], "decisions": ["b"], '
        '"action_items": [{"description": "c", "owner": "unassigned"}]}\n```'
    )
    envelope = {"output": {"message": {"content": [{"text": fenced_text}]}}}

    with patch("app.services.llm_client.boto3.client") as mock_client_factory:
        mock_instance = MagicMock()
        mock_instance.invoke_model.return_value = {
            "body": BytesIO(json_module.dumps(envelope).encode())
        }
        mock_client_factory.return_value = mock_instance

        result = summarize("some transcript text")

    assert result["key_points"] == ["a"]
    assert result["action_items"][0]["owner"] == "unassigned"


def test_summarize_raises_llm_error_on_empty_model_text(monkeypatch):
    import json as json_module
    from io import BytesIO
    from unittest.mock import MagicMock, patch

    envelope = {"output": {"message": {"content": [{"text": ""}]}}}

    with patch("app.services.llm_client.boto3.client") as mock_client_factory:
        mock_instance = MagicMock()
        mock_instance.invoke_model.return_value = {
            "body": BytesIO(json_module.dumps(envelope).encode())
        }
        mock_client_factory.return_value = mock_instance

        with pytest.raises(LLMError, match="empty response"):
            summarize("some transcript text")
