import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import summaries
from app.storage.sqlite_impl import SQLiteRepository


def _mock_bedrock_body(key_points, decisions, action_items):
    """Builds a fake Bedrock invoke_model response matching Nova's Converse-style shape."""
    inner_text = json.dumps(
        {"key_points": key_points, "decisions": decisions, "action_items": action_items}
    )
    payload = {"output": {"message": {"content": [{"text": inner_text}]}}}
    return {"body": BytesIO(json.dumps(payload).encode())}


@pytest.fixture
def mock_bedrock_success():
    """Patches boto3 so llm_client.summarize() returns a canned successful result."""
    with patch("app.services.llm_client.boto3.client") as mock_client_factory:
        mock_instance = MagicMock()
        mock_instance.invoke_model.return_value = _mock_bedrock_body(
            key_points=["Q4 targets on track"],
            decisions=["Approved budget increase"],
            action_items=[
                {"description": "Finalize marketing strategy", "owner": "Sarah Chen"},
                {"description": "Update timeline", "owner": "unassigned"},
            ],
        )
        mock_client_factory.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_bedrock_timeout():
    from botocore.exceptions import ReadTimeoutError

    with patch("app.services.llm_client.boto3.client") as mock_client_factory:
        mock_instance = MagicMock()
        mock_instance.invoke_model.side_effect = ReadTimeoutError(
            endpoint_url="https://bedrock-runtime.example.com"
        )
        mock_client_factory.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_bedrock_malformed():
    """A syntactically valid Bedrock envelope, but the model's JSON text is
    missing the required key_points/decisions/action_items shape."""
    with patch("app.services.llm_client.boto3.client") as mock_client_factory:
        mock_instance = MagicMock()
        inner_text = json.dumps({"unexpected": "shape"})
        envelope = {"output": {"message": {"content": [{"text": inner_text}]}}}
        mock_instance.invoke_model.return_value = {
            "body": BytesIO(json.dumps(envelope).encode())
        }
        mock_client_factory.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def in_memory_storage(tmp_path):
    """A real SQLite repository backed by a throwaway file per test."""
    db_file = tmp_path / "test.db"
    return SQLiteRepository(db_path=str(db_file))


@pytest.fixture
def client(in_memory_storage):
    """FastAPI TestClient with storage dependency overridden (no real app startup)."""
    from fastapi import FastAPI

    app = FastAPI()
    app.dependency_overrides[summaries.get_storage] = lambda: in_memory_storage
    app.include_router(summaries.router)
    return TestClient(app)
