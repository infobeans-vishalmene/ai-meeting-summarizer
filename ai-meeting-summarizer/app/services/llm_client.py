"""
Centralized LLM client — the ONLY module allowed to call the LLM provider.
Per Constitution Principle I: "New features must never introduce direct LLM
provider imports or API calls. All interactions MUST go through the
designated LLM client module."

Provider: AWS Bedrock, model: Amazon Nova Lite, via a cross-region
inference profile (Nova models don't support on-demand invocation by
bare foundation-model ID). Swapping models/providers later means
changing this file only.

Per Constitution Principle III, every failure mode is caught explicitly —
no silent failures, no partial/garbled results returned to callers.
"""
import json
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError

MODEL_ID = "global.amazon.nova-2-lite-v1:0"
# Full inference profile ARN, confirmed via:
#   aws bedrock list-inference-profiles --region us-east-1
# Nova models require an inference profile (not a bare foundation-model ID)
# for on-demand invocation; some accounts/SDK versions require the full ARN
# rather than the short "us.amazon.nova-lite-v1:0" form.
CLIENT_TIMEOUT_SECONDS = 50  # leaves 10s margin before the 60s endpoint timeout (NFR-003)

_SUMMARIZATION_PROMPT = """You are analyzing a meeting transcript. Extract exactly \
three things and return ONLY valid JSON (no markdown, no commentary):

{{
  "key_points": ["..."],
  "decisions": ["..."],
  "action_items": [{{"description": "...", "owner": "Name or unassigned"}}]
}}

Rules:
- For "owner": only use a name if it is EXPLICITLY stated in the transcript
  (e.g. "John will handle the report"). If no owner is clearly stated, use
  exactly the string "unassigned". Never guess based on tone or context.
- Do not include any text outside the JSON object.

Transcript:
{transcript}
"""


class LLMTimeoutError(Exception):
    """Raised when the Bedrock call exceeds CLIENT_TIMEOUT_SECONDS. Maps to 503."""


class LLMError(Exception):
    """Raised for malformed responses or non-timeout Bedrock errors. Maps to 500."""


def _get_client():
    config = Config(read_timeout=CLIENT_TIMEOUT_SECONDS, retries={"max_attempts": 0})
    return boto3.client(
        "bedrock-runtime",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        config=config,
    )


def summarize(transcript: str) -> dict:
    """
    Sends a transcript to Bedrock (Nova Lite) and returns structured data.

    Returns:
        dict with keys: key_points (list[str]), decisions (list[str]),
        action_items (list[dict] with "description" and "owner").

    Raises:
        LLMTimeoutError: Bedrock call exceeded the client timeout, or was throttled.
        LLMError: Bedrock returned an error, or its response could not be
            parsed into the expected structure.
    """
    client = _get_client()
    prompt = _SUMMARIZATION_PROMPT.format(transcript=transcript)

    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"temperature": 0.2, "maxTokens": 2000},
    }

    try:
        raw_response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
    except ReadTimeoutError as exc:
        raise LLMTimeoutError("Bedrock request timed out") from exc
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "ThrottlingException":
            raise LLMTimeoutError("Bedrock request throttled") from exc
        # ValidationException, InternalServerException, etc. -> 500 per plan.md
        raise LLMError(f"Bedrock client error: {error_code}") from exc

    return _parse_response(raw_response)


def _strip_markdown_fence(text: str) -> str:
    """
    Some models wrap JSON output in markdown code fences (```json ... ```)
    even when explicitly told not to. Strip that wrapping before parsing,
    rather than treating it as a hard failure.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove the opening fence (with optional language tag) and closing fence.
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else stripped
        if stripped.endswith("```"):
            stripped = stripped[: -3]
        stripped = stripped.strip()
    return stripped


def _parse_response(raw_response: dict) -> dict:
    """Parses and validates the Bedrock response shape. Raises LLMError on any
    deviation — a malformed response must never silently become a partial
    summary (per Constitution Principle III)."""
    try:
        payload = json.loads(raw_response["body"].read())
        model_text = payload["output"]["message"]["content"][0]["text"]
    except (KeyError, json.JSONDecodeError, IndexError) as exc:
        raise LLMError("Malformed response envelope from Bedrock") from exc

    if not model_text or not model_text.strip():
        raise LLMError("Bedrock returned an empty response")

    cleaned_text = _strip_markdown_fence(model_text)

    try:
        parsed = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise LLMError("Model output was not valid JSON") from exc

    required_keys = {"key_points", "decisions", "action_items"}
    if not required_keys.issubset(parsed.keys()):
        raise LLMError(f"Bedrock response missing required fields: {required_keys}")

    for item in parsed["action_items"]:
        if "description" not in item or "owner" not in item:
            raise LLMError("action_items entries must have description and owner")

    return parsed
