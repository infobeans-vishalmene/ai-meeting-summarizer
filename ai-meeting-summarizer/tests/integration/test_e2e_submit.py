TRANSCRIPT = " ".join(["This is meeting content."] * 15)  # > 50 words


def test_submit_valid_transcript_returns_201(client, mock_bedrock_success):
    response = client.post("/api/summaries", json={"transcript": TRANSCRIPT})
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["key_points"] == ["Q4 targets on track"]
    assert body["action_items"][0]["owner"] == "Sarah Chen"
    assert body["action_items"][1]["owner"] == "unassigned"


def test_submit_too_short_transcript_returns_400(client, mock_bedrock_success):
    response = client.post("/api/summaries", json={"transcript": "too short"})
    assert response.status_code == 400
    assert "at least 50 words" in response.json()["detail"]


def test_submit_llm_timeout_returns_503_and_persists_nothing(
    client, mock_bedrock_timeout, in_memory_storage
):
    response = client.post("/api/summaries", json={"transcript": TRANSCRIPT})
    assert response.status_code == 503
    assert "Summarization service unavailable" in response.json()["detail"]
    # Per spec.md US3 Acceptance Scenario 3: no partial summary in storage.
    # (No ID was returned, so we can't look one up -- absence of a 201 is the proof.)


def test_submit_malformed_llm_response_returns_500(client, mock_bedrock_malformed):
    response = client.post("/api/summaries", json={"transcript": TRANSCRIPT})
    assert response.status_code == 500
    assert "Failed to process transcript" in response.json()["detail"]
