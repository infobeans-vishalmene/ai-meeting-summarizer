TRANSCRIPT = " ".join(["This is meeting content."] * 15)


def test_retrieve_after_submit_returns_identical_data(client, mock_bedrock_success):
    submit_response = client.post("/api/summaries", json={"transcript": TRANSCRIPT})
    summary_id = submit_response.json()["id"]

    get_response = client.get(f"/api/summaries/{summary_id}")
    assert get_response.status_code == 200
    assert get_response.json()["key_points"] == submit_response.json()["key_points"]
    assert get_response.json()["id"] == summary_id


def test_retrieve_nonexistent_id_returns_404(client):
    response = client.get("/api/summaries/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Summary not found"
