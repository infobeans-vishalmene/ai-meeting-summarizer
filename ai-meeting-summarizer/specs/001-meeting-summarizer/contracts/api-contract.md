# API Contract: Meeting Notes Summarizer

**Date**: 2026-09-11  
**Phase**: Phase 1 (Design)  
**Format**: OpenAPI 3.0 (simplified)

## Overview

Two endpoints provide the core MVP functionality:
1. `POST /api/summaries` — Submit transcript, receive processed summary
2. `GET /api/summaries/{id}` — Retrieve previously stored summary

Both endpoints:
- Accept/return JSON only
- Require no authentication
- Implement explicit error handling per Constitution Principle III

---

## Endpoint 1: Submit Transcript

**Method**: `POST`  
**Path**: `/api/summaries`  
**Content-Type**: `application/json`

### Request Body

```json
{
  "transcript": "string (required): Raw meeting transcript, plain text. Length: 50-10,000 words."
}
```

### Response: Success (201 Created)

**Status Code**: `201`

**Content-Type**: `application/json`

**Body**: [See data-model.md for Summary entity schema]

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript_excerpt": "Raw meeting transcript text here...",
  "transcript_length_words": 245,
  "key_points": [
    "Q4 targets are on track",
    "New feature launch delayed by 2 weeks"
  ],
  "decisions": [
    "Approve budget increase for marketing team",
    "Move launch date to March 15"
  ],
  "action_items": [
    {
      "description": "Finalize Q4 marketing strategy",
      "owner": "Sarah Chen"
    },
    {
      "description": "Update project timeline in Jira",
      "owner": "unassigned"
    }
  ],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Response: Validation Errors (400 Bad Request)

**Status Code**: `400`

**Content-Type**: `application/json`

**Scenarios**:

1. **Empty/Whitespace Transcript**
```json
{
  "error": "Transcript cannot be empty",
  "code": "EMPTY_TRANSCRIPT"
}
```

2. **Transcript Too Short (<50 words)**
```json
{
  "error": "Transcript must contain at least 50 words",
  "code": "TRANSCRIPT_TOO_SHORT"
}
```

3. **Transcript Too Long (>10,000 words)**
```json
{
  "error": "Transcript exceeds maximum length of 10,000 words",
  "code": "TRANSCRIPT_TOO_LONG"
}
```

4. **Invalid JSON**
```json
{
  "error": "Invalid JSON in request body",
  "code": "INVALID_JSON"
}
```

### Response: LLM Processing Timeout (503 Service Unavailable)

**Status Code**: `503`

**Content-Type**: `application/json`

**Scenario**: LLM API call or processing exceeds 60-second timeout

```json
{
  "error": "Summarization service unavailable; please try again later",
  "code": "LLM_TIMEOUT"
}
```

*Note: No partial summary is persisted; status 503 indicates no data was saved.*

### Response: LLM Processing Error (500 Internal Server Error)

**Status Code**: `500`

**Content-Type**: `application/json`

**Scenario**: LLM returns malformed response, or other unrecoverable error occurs

```json
{
  "error": "Failed to process transcript; please contact support",
  "code": "PROCESSING_FAILED"
}
```

*Note: API keys, credentials, full transcript content, or LLM error details are NOT included in response (Principle II).*

---

## Endpoint 2: Retrieve Summary

**Method**: `GET`  
**Path**: `/api/summaries/{id}`  
**Path Parameter**: `id` (UUID string)

### Response: Success (200 OK)

**Status Code**: `200`

**Content-Type**: `application/json`

**Body**: [See data-model.md for Summary entity schema]

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript_excerpt": "Raw meeting transcript text here...",
  "transcript_length_words": 245,
  "key_points": [...],
  "decisions": [...],
  "action_items": [...],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Response: Not Found (404 Not Found)

**Status Code**: `404`

**Content-Type**: `application/json`

**Scenario**: Summary with given ID does not exist

```json
{
  "error": "Summary not found",
  "code": "SUMMARY_NOT_FOUND"
}
```

### Response: Invalid ID Format (400 Bad Request)

**Status Code**: `400`

**Content-Type**: `application/json`

**Scenario**: ID parameter is not a valid UUID

```json
{
  "error": "Invalid ID format; expected UUID",
  "code": "INVALID_ID_FORMAT"
}
```

---

## Shared Error Format

All error responses follow this structure:

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "timestamp": "2026-09-11T14:32:00Z"
}
```

**Fields**:
- `error` (string): User-facing description
- `code` (string): Stable error code for client-side handling
- `timestamp` (ISO 8601): When the error occurred (server time)

**Security**: No API keys, request bodies (especially transcripts), or stack traces are included in error responses (Principle II).

---

## Implementation Notes

1. **Framework**: FastAPI with Pydantic validation
2. **Type Hints**: All request/response models MUST include complete type hints (Principle V)
3. **Error Handler**: Middleware sanitizes errors before returning (no API keys, tokens, or full transcript content in responses; Principle II)
4. **Bedrock Integration**: POST handler calls centralized LLM client (`app/services/llm_client.py`) which wraps Bedrock (Principle I); explicit exception handling for timeouts (50s) and malformed responses (Principle III)
5. **Storage**: Both endpoints access storage via repository pattern (`app/storage/repository.py`) abstracted behind interface (Principle IV)
6. **Logging**: All errors logged with sanitized output; request ID used instead of full content
7. **Timeout Handling**: POST endpoint must enforce 60-second timeout and return 503 if exceeded (NFR-003); Bedrock client timeout set to 50s
8. **Retrieval Performance**: GET endpoint must complete in <500ms (NFR-004); SQLite index recommended on `id` column
9. **Test Coverage**: All endpoints MUST have corresponding test cases (unit, integration, contract) with mocked Bedrock (Principle V)

---

## Request/Response Examples

### Example 1: Successful Summarization

**Request**:
```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "In this meeting we discussed Q4 targets, budget, and feature launch timeline. Sarah will finalize the marketing strategy. James will coordinate testing. We decided to move launch from Feb 28 to Mar 15 and approved marketing budget increase."
  }'
```

**Response** (201):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "transcript_excerpt": "In this meeting we discussed Q4 targets, budget, and feature launch timeline...",
  "transcript_length_words": 45,
  "key_points": [...],
  "decisions": [...],
  "action_items": [...],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Example 2: Transcript Too Short

**Request**:
```bash
curl -X POST http://localhost:8000/api/summaries \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Brief discussion about Q4"}'
```

**Response** (400):
```json
{
  "error": "Transcript must contain at least 50 words",
  "code": "TRANSCRIPT_TOO_SHORT",
  "timestamp": "2026-09-11T14:32:00Z"
}
```

### Example 3: Retrieve Existing Summary

**Request**:
```bash
curl -X GET http://localhost:8000/api/summaries/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response** (200):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "transcript_excerpt": "In this meeting we discussed Q4 targets...",
  "transcript_length_words": 245,
  "key_points": [...],
  "decisions": [...],
  "action_items": [...],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Example 4: Retrieve Non-Existent Summary

**Request**:
```bash
curl -X GET http://localhost:8000/api/summaries/nonexistent-id
```

**Response** (404):
```json
{
  "error": "Summary not found",
  "code": "SUMMARY_NOT_FOUND",
  "timestamp": "2026-09-11T14:32:00Z"
}
```
