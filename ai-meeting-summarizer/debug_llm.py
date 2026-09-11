"""
Temporary debug script — NOT part of the spec/tasks, just for diagnosing
the real Bedrock response shape. Delete this once the real issue is found;
don't leave it lying around long-term (it deliberately prints raw model
output, which error_handler.py exists specifically to avoid doing in the
real app).

Run: python debug_llm.py
"""
import json

import boto3

from app.services.llm_client import MODEL_ID, _SUMMARIZATION_PROMPT

transcript = " ".join(["This is a test meeting about the budget."] * 15)
prompt = _SUMMARIZATION_PROMPT.format(transcript=transcript)

client = boto3.client("bedrock-runtime", region_name="us-east-1")

body = {
    "messages": [{"role": "user", "content": [{"text": prompt}]}],
    "inferenceConfig": {"temperature": 0.2, "maxTokens": 2000},
}

print("--- Calling Bedrock directly ---")
try:
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    raw = json.loads(response["body"].read())
    print("--- RAW FULL RESPONSE ---")
    print(json.dumps(raw, indent=2))

    print("\n--- EXTRACTED MODEL TEXT ---")
    model_text = raw["output"]["message"]["content"][0]["text"]
    print(repr(model_text))  # repr() shows exact chars, e.g. markdown fences/newlines

except Exception as exc:
    print(f"\n--- EXCEPTION ---\n{type(exc).__name__}: {exc}")
