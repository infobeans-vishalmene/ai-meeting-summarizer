# Quickstart: Validation & Test Scenarios

**Date**: 2026-09-11  
**Phase**: Phase 1 (Design)  
**Purpose**: Validation guide to test the Meeting Notes Summarizer feature end-to-end

---

## Prerequisites

- **API Server**: FastAPI application running (default: `http://localhost:8000`)
- **HTTP Client**: curl, Postman, or equivalent for making requests
- **AWS Credentials**: Configured via standard boto3 credential chain (environment variables, `~/.aws/credentials`, or IAM role)
- **AWS Region**: Set to a region supporting Amazon Bedrock (e.g., `us-east-1`, `us-west-2`, `eu-west-1`)
- **Database**: SQLite (`sqlite.db`) must be accessible and initialized with schema
- **Python Environment**: Python 3.11+ with all dependencies from `requirements.txt` installed
- **Testing**: pytest and mocking fixtures available for running test suite

---

## Test Scenario 1: Successful Summarization (Happy Path)

**Objective**: Verify that a valid transcript is successfully processed and summary is returned with all expected fields.

### Setup

Create a test transcript file (`test_transcript.txt`):
```
In today's Q4 planning meeting, we discussed three main topics: revenue targets, feature roadmap, and team capacity. 

John Chen reviewed the revenue targets and confirmed we're on track to hit 150% of Q3 numbers. We decided to allocate 40% of the increase to R&D. Sarah Martinez will finalize the budget breakdown and communicate it to finance by Friday.

On the feature roadmap, we identified three critical features for Q4: API v2, mobile app improvements, and analytics dashboard. The mobile app work is scheduled to start in October. James Rodriguez volunteered to lead the analytics dashboard project and will post a detailed timeline tomorrow.

For team capacity, we acknowledged that the current team is at 85% utilization. We decided to hire two additional engineers before Q4 and one product manager. HR will begin recruiting immediately. David will coordinate with hiring.

Action items: Sarah - finalize budget, James - post analytics dashboard timeline, David - coordinate hiring process. Meeting concluded with agreement to reconvene in two weeks.
```

**Word count**: ~160 words ✓ (within 50-10,000 range)

### Execute

**Request**:
```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "transcript": "$(cat test_transcript.txt)"
}
EOF
```

**Alternative (inline)**:
```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "In today'"'"'s Q4 planning meeting... [full transcript text]"
  }'
```

### Expected Response (201 Created)

```json
{
  "id": "<UUID>",
  "transcript_excerpt": "In today's Q4 planning meeting, we discussed...",
  "transcript_length_words": 160,
  "key_points": [
    "Q4 revenue targets on track for 150% of Q3",
    "Mobile app work starts in October",
    "Team at 85% utilization; hiring two engineers + PM"
  ],
  "decisions": [
    "Allocate 40% of revenue increase to R&D",
    "Implement API v2, mobile improvements, analytics dashboard in Q4",
    "Hire two additional engineers and one product manager before Q4"
  ],
  "action_items": [
    {
      "description": "Finalize budget breakdown and communicate to finance",
      "owner": "Sarah Martinez"
    },
    {
      "description": "Post detailed timeline for analytics dashboard project",
      "owner": "James Rodriguez"
    },
    {
      "description": "Coordinate hiring process for two engineers and one PM",
      "owner": "David"
    }
  ],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Validation Checklist

- [ ] HTTP status is 201
- [ ] Response contains all fields: `id`, `transcript_excerpt`, `transcript_length_words`, `key_points`, `decisions`, `action_items`, `created_at`, `source`
- [ ] `id` is a valid UUID
- [ ] `transcript_length_words` matches actual word count (160)
- [ ] `key_points` contains 2-5 distinct discussion points extracted from transcript
- [ ] `decisions` lists explicit decisions (e.g., budget allocation, hiring approval)
- [ ] `action_items` includes all tasks with assigned owners (no unassigned items here since all are explicitly mentioned)
- [ ] `created_at` is ISO 8601 format (e.g., `2026-09-11T14:32:00Z`)
- [ ] No API keys, credentials, or full transcript appear in response

**Save the returned `id` for use in Scenario 2.**

---

## Test Scenario 2: Retrieve Stored Summary

**Objective**: Verify that a previously submitted summary can be retrieved by ID with all data intact.

### Execute

Use the `id` from Scenario 1:

```bash
curl -X GET http://localhost:8000/api/summaries/<ID_FROM_SCENARIO_1>
```

### Expected Response (200 OK)

```json
{
  "id": "<SAME_UUID_FROM_SCENARIO_1>",
  "transcript_excerpt": "In today's Q4 planning meeting, we discussed...",
  "transcript_length_words": 160,
  "key_points": [...],
  "decisions": [...],
  "action_items": [...],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Validation Checklist

- [ ] HTTP status is 200
- [ ] All fields returned match the POST response from Scenario 1
- [ ] No data loss or corruption occurred
- [ ] `created_at` timestamp unchanged

---

## Test Scenario 3: Transcript Too Short (<50 words)

**Objective**: Verify that transcripts with fewer than 50 words are rejected with appropriate error.

### Execute

```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Discussed Q4 targets with Sarah and James. Approved budget."
  }'
```

**Word count**: ~10 words ✗ (below 50-word minimum)

### Expected Response (400 Bad Request)

```json
{
  "error": "Transcript must contain at least 50 words",
  "code": "TRANSCRIPT_TOO_SHORT",
  "timestamp": "2026-09-11T14:32:00Z"
}
```

### Validation Checklist

- [ ] HTTP status is 400
- [ ] Error message mentions 50-word minimum
- [ ] Error code is `TRANSCRIPT_TOO_SHORT`
- [ ] No summary is created; verify by noting that no ID is returned

---

## Test Scenario 4: Transcript Too Long (>10,000 words)

**Objective**: Verify that transcripts exceeding 10,000 words are rejected with appropriate error.

### Execute

Create a long transcript (11,000+ words) and submit:

```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "[Very long transcript with >10,000 words]"
  }'
```

### Expected Response (400 Bad Request)

```json
{
  "error": "Transcript exceeds maximum length of 10,000 words",
  "code": "TRANSCRIPT_TOO_LONG",
  "timestamp": "2026-09-11T14:32:00Z"
}
```

### Validation Checklist

- [ ] HTTP status is 400
- [ ] Error message mentions 10,000-word maximum
- [ ] Error code is `TRANSCRIPT_TOO_LONG`
- [ ] No summary is created

---

## Test Scenario 5: Empty/Whitespace Transcript

**Objective**: Verify that empty or whitespace-only inputs are rejected.

### Execute

```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{"transcript": "   \n\t  "}'
```

### Expected Response (400 Bad Request)

```json
{
  "error": "Transcript cannot be empty",
  "code": "EMPTY_TRANSCRIPT",
  "timestamp": "2026-09-11T14:32:00Z"
}
```

### Validation Checklist

- [ ] HTTP status is 400
- [ ] Error code is `EMPTY_TRANSCRIPT`

---

## Test Scenario 6: Non-Existent Summary ID

**Objective**: Verify that retrieving a summary with an invalid or non-existent ID returns 404.

### Execute

```bash
curl -X GET http://localhost:8000/api/summaries/00000000-0000-0000-0000-000000000000
```

### Expected Response (404 Not Found)

```json
{
  "error": "Summary not found",
  "code": "SUMMARY_NOT_FOUND",
  "timestamp": "2026-09-11T14:32:00Z"
}
```

### Validation Checklist

- [ ] HTTP status is 404
- [ ] Error code is `SUMMARY_NOT_FOUND`

---

## Test Scenario 7: Action Items with No Clear Owner

**Objective**: Verify that action items without explicit owner attribution are marked "unassigned".

### Setup

Create a transcript where some action items lack clear owner attribution:

```
Meeting notes: We discussed three action items. First, Sarah will finalize the proposal. Second, the team should review the documentation. Third, David will send the final report.
```

### Execute

```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Meeting notes: We discussed three action items. First, Sarah will finalize the proposal. Second, the team should review the documentation. Third, David will send the final report."
  }'
```

### Expected Response (201 Created)

```json
{
  "action_items": [
    {
      "description": "Finalize the proposal",
      "owner": "Sarah"
    },
    {
      "description": "Review the documentation",
      "owner": "unassigned"
    },
    {
      "description": "Send the final report",
      "owner": "David"
    }
  ]
}
```

### Validation Checklist

- [ ] HTTP status is 201
- [ ] Action item 1 has owner "Sarah" (explicit mention)
- [ ] Action item 2 has owner "unassigned" (passive voice "should review" with no clear owner)
- [ ] Action item 3 has owner "David" (explicit mention)

---

## Integration Test Checklist

Run the pytest test suite to validate:

```bash
pytest tests/integration/test_e2e_submit.py::test_successful_summarization
pytest tests/integration/test_e2e_submit.py::test_transcript_too_short
pytest tests/integration/test_e2e_submit.py::test_transcript_too_long
pytest tests/integration/test_e2e_submit.py::test_empty_transcript
pytest tests/integration/test_e2e_retrieve.py::test_retrieve_existing_summary
pytest tests/integration/test_e2e_retrieve.py::test_retrieve_nonexistent_summary
pytest tests/contract/test_api_contract.py::test_response_schema_compliance
```

### Constitution Compliance Checks

- [ ] **Principle I (LLM Centralization)**: Verify that handler routes through centralized LLM client (check logs/trace)
- [ ] **Principle II (Security)**: Verify that error responses never include API keys, credentials, or full transcript text
- [ ] **Principle III (Explicit Failure)**: Simulate LLM timeout/error and verify clear 503/500 response is returned
- [ ] **Principle IV (Storage Abstraction)**: Verify that business logic uses storage interface only (no DB-specific queries in handler/service)
- [ ] **Principle V (Code Quality)**: Verify that all functions have type hints and 100% test coverage

---

## Reference

See [api-contract.md](api-contract.md) for complete endpoint specifications.  
See [data-model.md](data-model.md) for Summary entity schema.
