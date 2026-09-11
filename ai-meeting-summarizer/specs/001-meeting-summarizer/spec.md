# Feature Specification: Meeting Notes Summarizer

**Feature Branch**: `001-meeting-summarizer`

**Created**: 2026-09-11

**Status**: Draft

**Input**: Build an AI Meeting Notes Summarizer. A user submits a raw meeting transcript (plain text) via an API endpoint. The service sends the transcript to an LLM and returns a structured summary containing: key discussion points, decisions made, and action items with an assigned owner where mentioned in the transcript. The summary is stored and can be retrieved later by its ID.

## Clarifications

### Session 2026-09-11

- Q: Does the API endpoint require any form of authentication? → A: No authentication required; endpoints are completely open/unauthenticated
- Q: Should the API accept and return request/response bodies as JSON only? → A: JSON only (request body and responses)
- Q: Should the POST `/api/summaries` endpoint process synchronously or asynchronously? → A: Synchronous processing with 60-second timeout
- Q: How long should completed summaries be retained in storage? → A: Retain indefinitely; no automatic deletion or archival for MVP
- Q: Should there be a minimum length requirement for transcripts? → A: Require minimum 50 words to ensure meaningful meeting content

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit Meeting Transcript for Summarization (Priority: P1)

A user has a raw meeting transcript (plain text) and wants to submit it to the system for automatic summarization. The system processes the transcript through an LLM to extract key insights and action items, then returns the processed summary with a unique ID.

**Why this priority**: This is the core MVP feature. Without the ability to submit and summarize transcripts, the entire product has no value. This is the critical path.

**Independent Test**: Can be fully tested by submitting a valid transcript and verifying that the API returns a properly structured summary object with all required fields (key_points, decisions, action_items, id).

**Acceptance Scenarios**:

1. **Given** a valid meeting transcript under 10,000 words and at least 50 words, **When** user POST the transcript to `/api/summaries`, **Then** the system returns a 201 response with a summary object containing `id`, `transcript_excerpt`, `key_points`, `decisions`, and `action_items`
2. **Given** a transcript with clearly identified action items and owners, **When** the summary is returned, **Then** each action item includes the assigned owner's name
3. **Given** a transcript with action items but no clear owner attribution, **When** the summary is returned, **Then** those action items are marked with owner: "unassigned"
4. **Given** a transcript that exceeds 10,000 words, **When** user submits it, **Then** the system returns a 400 error with message "Transcript exceeds maximum length of 10,000 words"
5. **Given** a transcript with fewer than 50 words, **When** user submits it, **Then** the system returns a 400 error with message "Transcript must contain at least 50 words"

---

### User Story 2 - Retrieve Stored Summary by ID (Priority: P1)

A user has previously submitted a transcript and wants to retrieve the generated summary using the ID returned from the initial submission. The system fetches and returns the stored summary data.

**Why this priority**: This is equally critical to submission. The entire value of storing summaries is lost if they cannot be retrieved. Together with Story 1, this forms the complete MVP loop.

**Independent Test**: Can be fully tested by retrieving a previously stored summary by ID and verifying all fields are returned intact.

**Acceptance Scenarios**:

1. **Given** a summary ID from a prior submission, **When** user GET `/api/summaries/{id}`, **Then** the system returns a 200 response with the complete summary object
2. **Given** a nonexistent summary ID, **When** user attempts to retrieve it, **Then** the system returns 404 with message "Summary not found"
3. **Given** a valid summary ID, **When** retrieved, **Then** all original data (key_points, decisions, action_items) is returned exactly as stored

---

### User Story 3 - Handle LLM Processing Failures Gracefully (Priority: P1)

The system must handle LLM service failures, timeouts, and malformed responses without returning partial or corrupted summaries to the user. The user receives a clear, actionable error message.

**Why this priority**: This is non-negotiable per the project constitution (Principle III). Failure to handle LLM errors explicitly could result in silent failures or garbled data. This directly impacts data integrity and user trust.

**Independent Test**: Can be fully tested by simulating LLM timeout/error conditions and verifying that the user receives a clear error response and no partial summary is stored.

**Acceptance Scenarios**:

1. **Given** an LLM API timeout during transcript processing, **When** the timeout is detected, **Then** the system returns a 503 error with message "Summarization service unavailable; please try again later"
2. **Given** an LLM API returns a malformed response, **When** the response is received, **Then** the system rejects it, logs the error (without including API keys or transcript content), and returns 500 with message "Failed to process transcript; please contact support"
3. **Given** an LLM processing failure, **When** the user checks the summary by ID, **Then** no partial or corrupted summary exists in storage

---

### Edge Cases

- How does the system handle transcripts with special characters, emojis, or non-ASCII text? (Should accept as-is and pass to LLM for processing)
- What is the maximum reasonable size for a single action item or decision entry extracted by the LLM? (No hard limit; design for practical UI rendering, e.g., 500 characters)
- How does the system handle concurrent submissions of the same or very similar transcripts? (Process independently; no deduplication; database locking handles concurrent writes)
- What happens if a summary retrieval request comes in while an LLM is still processing the initial submission? (Synchronous model prevents this; retrieval only works after POST completes)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept POST requests to `/api/summaries` with a raw meeting transcript in the request body
- **FR-002**: System MUST validate that the submitted transcript does not exceed 10,000 words; if it does, reject with a 400 status and descriptive error message
- **FR-003**: System MUST reject empty or whitespace-only transcripts with a 400 status and message "Transcript cannot be empty"
- **FR-004**: System MUST route the validated transcript to the centralized LLM client module (per Constitution Principle I)
- **FR-005**: System MUST explicitly handle LLM API timeouts and return a 503 error with user-facing message (per Constitution Principle III)
- **FR-006**: System MUST explicitly handle malformed or invalid LLM responses and return a 500 error without exposing API details (per Constitution Principle III)
- **FR-007**: System MUST parse the LLM response to extract three structured sections: key discussion points, decisions made, and action items
- **FR-008**: System MUST identify action item owners from the transcript; if no owner is clearly stated, mark the action item with owner: "unassigned" (not guessed or inferred)
- **FR-009**: System MUST sanitize all error logs to exclude API keys, credentials, and full transcript content (per Constitution Principle II)
- **FR-010**: System MUST persist the generated summary with a unique ID in the storage layer
- **FR-011**: System MUST use the abstract storage interface to persist summaries; business logic must not assume a specific database (per Constitution Principle IV)
- **FR-012**: System MUST support retrieval of stored summaries via GET `/api/summaries/{id}` and return a 200 with the summary object
- **FR-013**: System MUST return 404 with message "Summary not found" when retrieving a non-existent summary ID
- **FR-014**: System MUST store summary metadata: `id` (unique identifier), `created_at` (timestamp), `transcript_length` (word count), and `key_points`, `decisions`, `action_items` (structured data)
- **FR-015**: System MUST validate that the submitted transcript contains at least 50 words; if it contains fewer, reject with a 400 status and message "Transcript must contain at least 50 words"

### Non-Functional Requirements

- **NFR-001**: All endpoints MUST include complete type hints for request/response parameters (per Constitution Principle V)
- **NFR-002**: All business logic and endpoint handlers MUST have corresponding test coverage (per Constitution Principle V)
- **NFR-003**: Processing a transcript of 10,000 words MUST complete within 60 seconds (including LLM latency), or the operation times out and returns 503
- **NFR-004**: Summary retrieval by ID MUST complete in under 500ms

### Out of Scope

- User authentication and authorization (no auth required for MVP)
- Editing or updating summaries after creation
- Real-time or streaming summarization
- Batch processing of multiple transcripts in a single request
- Filtering, searching, or listing all summaries

## Success Criteria *(mandatory)*

1. **Core Functionality**: Users can submit a meeting transcript via API and receive a structured summary with key points, decisions, and action items within 60 seconds
2. **Data Integrity**: All submitted summaries are persisted and can be retrieved exactly as generated (no data loss or corruption)
3. **Error Resilience**: When the LLM service fails or times out, users receive a clear, actionable error message; no partial or corrupted data is stored
4. **Security Compliance**: No API keys, credentials, or full transcripts appear in logs, error messages, or responses (per Constitution Principle II)
5. **Code Quality**: 100% of new functions include type hints and comprehensive test coverage (per Constitution Principle V)
6. **Owner Attribution Accuracy**: Action items without a clearly stated owner in the transcript are marked "unassigned" rather than incorrectly guessed
7. **Input Validation**: Transcripts exceeding 10,000 words are rejected immediately with a clear error; no truncation or silent rejection

## Key Entities

### Summary

- **id** (string, UUID): Unique identifier for the summary
- **transcript_excerpt** (string): First 200 characters of the submitted transcript (for context)
- **transcript_length_words** (integer): Word count of the original transcript
- **key_points** (array of strings): Extracted key discussion points from the transcript
- **decisions** (array of strings): Decisions made during the meeting
- **action_items** (array of objects):
  - **description** (string): What needs to be done
  - **owner** (string): Name of the person assigned; "unassigned" if not clearly stated in transcript
  - **priority** (string, optional): "high", "medium", "low" if determinable; omit if not stated
- **created_at** (ISO 8601 timestamp): When the summary was generated
- **source** (enum): "api" (for this MVP)

### API Request/Response Examples

**POST /api/summaries**

Request:
```json
{
  "transcript": "Raw meeting transcript text here..."
}
```

Response (201 Created):
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
  "created_at": "2026-09-11T14:32:00Z"
}
```

**GET /api/summaries/{id}**

Response (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript_excerpt": "Raw meeting transcript text here...",
  "transcript_length_words": 245,
  "key_points": [...],
  "decisions": [...],
  "action_items": [...],
  "created_at": "2026-09-11T14:32:00Z"
}
```

## Assumptions

1. **Transcript Format**: Transcripts are plain text; no HTML, Markdown, or special formatting is required (simplifies parsing)
2. **Word Count Definition**: Word count is calculated as space-separated tokens; exact algorithm can be tuned during implementation
3. **Minimum Transcript Length**: Transcripts must contain at least 50 words to ensure meaningful meeting content; shorter transcripts are rejected at validation
4. **API Payload Format**: All request and response bodies are JSON only; no alternative formats (form-encoded, XML, etc.) are supported for MVP
5. **API Authentication**: No authentication or authorization is required for MVP; endpoints are completely open/unauthenticated
6. **Processing Model**: Summary processing is synchronous; the API endpoint blocks until processing completes or times out after 60 seconds
7. **LLM Response Structure**: The LLM will reliably return structured output (either JSON or parseable text) with clear sections for points, decisions, and action items
8. **Owner Identification**: Owner names appear explicitly in the transcript (e.g., "John will handle the report"); passive voice or pronouns ("it will be handled") are not inferred as assignments
9. **Summary Uniqueness**: Each submission generates a unique summary even if the transcript is identical to a prior one (no deduplication)
10. **Storage Durability**: Summaries persist indefinitely unless explicitly deleted (not covered in this MVP, but assumed for future phases)
11. **Timestamp Accuracy**: Server timestamps in ISO 8601 format are sufficient; no timezone conversion is needed for MVP
12. **Concurrency**: The system does not need to handle the same user submitting the identical transcript simultaneously; standard database row locking is acceptable

## Dependencies

- **LLM Client Module**: Centralized LLM client module must be available and working (defined elsewhere in the codebase per Constitution Principle I)
- **Storage Interface**: Abstract storage layer must be implemented and support basic CRUD operations for summaries (per Constitution Principle IV)
- **HTTP Framework**: An existing API framework must be available to define endpoints

## Open Questions

None at this time. All key decisions have been made based on the user description and project constitution principles. The scope is well-defined, constraints are explicit, and out-of-scope items are clearly listed.
