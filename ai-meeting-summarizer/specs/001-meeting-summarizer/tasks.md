# Tasks: Meeting Notes Summarizer

**Input**: Design documents from `/specs/001-meeting-summarizer/`

**Prerequisites**: 
- plan.md (tech stack: FastAPI, boto3 Bedrock, SQLite, pytest)
- spec.md (3 user stories, all P1)
- data-model.md (Summary entity, ActionItem nested entity)
- contracts/api-contract.md (endpoint specifications)
- research.md (5 resolved decisions)

**Testing**: Tests REQUIRED per NFR-002 (100% coverage for endpoints/services)

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- All paths assume single-project structure under repository root: `app/`, `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, database schema

- [ ] T001 Create project directory structure: `app/`, `app/api/`, `app/api/routes/`, `app/services/`, `app/storage/`, `app/models/`, `app/middleware/`, `app/utils/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [ ] T002 Create `requirements.txt` with dependencies: fastapi, uvicorn, boto3, sqlalchemy, pydantic, pytest, pytest-cov, python-dotenv
- [ ] T003 Create `.env.example` with template variables: `AWS_REGION=us-east-1`, `AWS_ACCESS_KEY_ID=***`, `AWS_SECRET_ACCESS_KEY=***`
- [ ] T004 Create `.gitignore`: ignore `sqlite.db`, `.env`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.coverage`
- [ ] T005 Create `app/__init__.py` (empty)
- [ ] T006 Create `app/main.py`: FastAPI app initialization with error middleware import
- [ ] T007 [P] Create SQLite schema initialization script in `app/storage/schema.sql` with CREATE TABLE summaries statement (columns: id TEXT PRIMARY KEY, transcript_excerpt TEXT, transcript_length_words INTEGER, key_points JSON, decisions JSON, action_items JSON, created_at DATETIME, source TEXT)

---

## Phase 2: Foundational (Blocking Prerequisites - MUST complete before user stories)

**Purpose**: Core infrastructure that ALL user stories depend on. No user story work can begin until this phase is complete.

### Error Handling & Logging (Principle II - Security & Privacy)

- [ ] T008 Create `app/middleware/error_handler.py`: Middleware class that catches all exceptions, strips sensitive data (API keys, credentials, full transcripts), and returns sanitized error responses with error code and timestamp (never expose request body in error logs)
- [ ] T009 Create `app/utils/validation.py`: Validation functions:
  - `count_words(transcript: str) -> int`: Count space-separated words
  - `validate_transcript_length(transcript: str) -> tuple[bool, str]`: Check 50-10,000 word range; return (is_valid, error_message)
  - `validate_transcript_not_empty(transcript: str) -> tuple[bool, str]`: Check non-empty; return (is_valid, error_message)

### LLM Client (Principle I - LLM Centralization)

- [ ] T010 Create `app/services/llm_client.py`: Bedrock wrapper with:
  - `summarize(transcript: str) -> dict`: Single entry point for all LLM calls
    - Invoke boto3 bedrock-runtime client with model `amazon.nova-lite-v1:0`
    - Timeout: 50s (raising explicit timeout exception)
    - Return dict with keys: `key_points` (list), `decisions` (list), `action_items` (list of dicts with description, owner, priority)
  - Exception handling for: `ReadTimeoutError`, `ThrottlingException` (→ raise LLMTimeoutError), `ValidationException`, `InternalServerException` (→ raise LLMError), JSON parse errors (→ raise LLMMalformedResponseError)
  - Type hints on all parameters and return values

### Storage Layer (Principle IV - Storage Abstraction)

- [ ] T011 Create `app/storage/interface.py`: Abstract storage interface defining:
  - `create_summary(summary: dict) -> str`: Create summary; return UUID string
  - `get_summary(summary_id: str) -> dict | None`: Retrieve summary; return dict or None
  - Document that implementation must never expose DB-specific details to business logic

- [ ] T012 Create `app/storage/repository.py`: Repository pattern implementation using SQLAlchemy:
  - Import SummaryORM from models
  - `create_summary(summary_data: dict, session) -> str`: Insert row; return id
  - `get_summary(summary_id: str, session) -> dict | None`: Query by id; convert ORM to dict
  - Type hints on all functions

- [ ] T013 [P] Create `app/storage/sqlite_impl.py`: SQLite initialization:
  - `init_db(db_path: str)`: Create engine, session factory, run schema.sql
  - Return session factory function for dependency injection

### Data Models (Pydantic + SQLAlchemy ORM)

- [ ] T014 Create `app/models/summary.py`: Data models with:
  - **ActionItemResponse** (Pydantic): description (str, 1-500 chars), owner (str, 1-100 chars, required), priority (str | None, optional, enum: high/medium/low)
  - **SummaryResponse** (Pydantic): id (str), transcript_excerpt (str, max 200 chars), transcript_length_words (int, 50-10000), key_points (list[str]), decisions (list[str]), action_items (list[ActionItemResponse]), created_at (str, ISO 8601), source (str, "api")
  - **SummaryRequest** (Pydantic): transcript (str, required, trimmed)
  - **SummaryORM** (SQLAlchemy): Table mapping with JSON columns for key_points, decisions, action_items
  - All type hints required; Pydantic field validators for constraints

### Main Application Setup

- [ ] T015 Update `app/main.py`: 
  - Initialize FastAPI app with error_handler middleware
  - Configure database initialization on startup
  - Include route imports (to be created in user story phases)
  - Include logging configuration

**Checkpoint: Foundation complete** — All user stories can now proceed in parallel

---

## Phase 3: User Story 1 - Submit Meeting Transcript (Priority: P1) 🎯 MVP

**Goal**: User can submit a meeting transcript and receive a processed summary with key points, decisions, and action items

**Independent Test**: Submit valid 50-10,000 word transcript → receive 201 with summary object containing all required fields

### Tests for User Story 1 (Required - NFR-002)

- [ ] T016 [P] [US1] Create `tests/conftest.py`: pytest fixtures for:
  - Mock Bedrock client (boto3.client mock) returning valid summarization response
  - In-memory SQLite database (`:memory:`) for integration tests
  - FastAPI TestClient instance
  - Cleanup/reset DB between tests

- [ ] T017 [P] [US1] Create `tests/unit/test_validation.py`: Test validation functions:
  - `test_count_words_valid_transcript()`: Verify word count accuracy
  - `test_count_words_with_punctuation()`: Handle punctuation as single token
  - `test_validate_transcript_length_50_words()`: Pass exactly 50 words
  - `test_validate_transcript_length_10000_words()`: Pass exactly 10,000 words
  - `test_validate_transcript_length_too_short()`: Reject <50 words with error code TRANSCRIPT_TOO_SHORT
  - `test_validate_transcript_length_too_long()`: Reject >10,000 words with error code TRANSCRIPT_TOO_LONG
  - `test_validate_transcript_not_empty()`: Reject empty/whitespace strings with error code EMPTY_TRANSCRIPT

- [ ] T018 [P] [US1] Create `tests/unit/test_llm_client.py`: Test LLM client (with mocked Bedrock):
  - `test_summarize_valid_transcript()`: Mock Bedrock returns valid summary → llm_client returns dict with key_points, decisions, action_items
  - `test_summarize_bedrock_timeout()`: Mock ReadTimeoutError → llm_client raises LLMTimeoutError
  - `test_summarize_bedrock_throttle()`: Mock ThrottlingException → llm_client raises LLMTimeoutError (503 mapping)
  - `test_summarize_bedrock_validation_error()`: Mock ValidationException → llm_client raises LLMError
  - `test_summarize_bedrock_internal_error()`: Mock InternalServerException → llm_client raises LLMError
  - `test_summarize_malformed_json_response()`: Mock invalid JSON response → llm_client raises LLMMalformedResponseError

- [ ] T019 [P] [US1] Create `tests/unit/test_summarizer_service.py`: Test summarizer service (with mocked LLM & storage):
  - `test_process_transcript_valid()`: Happy path → returns summary dict with all fields
  - `test_process_transcript_too_short()`: Validation rejects <50 words before LLM call
  - `test_process_transcript_too_long()`: Validation rejects >10,000 words before LLM call
  - `test_process_transcript_empty()`: Validation rejects empty before LLM call
  - `test_process_transcript_action_item_owner_explicit()`: Extract owner name from transcript
  - `test_process_transcript_action_item_owner_unassigned()`: Mark "unassigned" when no explicit owner

- [ ] T020 [P] [US1] Create `tests/integration/test_e2e_submit.py`: Integration tests with test DB + mocked Bedrock:
  - `test_post_summaries_valid_transcript()`: POST valid transcript → 201 + summary object with all fields
  - `test_post_summaries_transcript_too_short()`: POST <50 words → 400 + error code TRANSCRIPT_TOO_SHORT
  - `test_post_summaries_transcript_too_long()`: POST >10,000 words → 400 + error code TRANSCRIPT_TOO_LONG
  - `test_post_summaries_empty_transcript()`: POST empty → 400 + error code EMPTY_TRANSCRIPT
  - `test_post_summaries_invalid_json()`: POST malformed JSON → 400 + error code INVALID_JSON
  - `test_post_summaries_bedrock_timeout()`: Mock Bedrock timeout → 503 + error code LLM_TIMEOUT + NO summary persisted
  - `test_post_summaries_bedrock_malformed_response()`: Mock Bedrock returns invalid JSON → 500 + error code PROCESSING_FAILED (no keys/transcripts in error)
  - `test_post_summaries_response_schema()`: Verify 201 response matches api-contract.md schema (id, transcript_excerpt, key_points, decisions, action_items with owner, created_at ISO 8601, source: "api")

- [ ] T021 [P] [US1] Create `tests/contract/test_api_contract.py`: Contract tests validating endpoint specifications from contracts/api-contract.md:
  - `test_post_summaries_request_schema()`: POST request must have transcript field (string, required)
  - `test_post_summaries_response_201_schema()`: 201 response must match SummaryResponse schema exactly
  - `test_post_summaries_response_400_schema()`: 400 response must have error, code, timestamp fields
  - `test_post_summaries_response_503_schema()`: 503 response must have error, code, timestamp fields
  - `test_post_summaries_response_500_schema()`: 500 response must have error, code, timestamp fields (no API keys/credentials/transcripts exposed)

### Implementation for User Story 1

- [ ] T022 Create `app/services/summarizer.py`: Core summarizer service:
  - `process_transcript(transcript: str, llm_client, repository) -> dict`: Main orchestration function
    - Validate transcript length (50-10,000 words) → raise ValueError if invalid
    - Validate transcript not empty → raise ValueError if invalid
    - Call llm_client.summarize(transcript) → handle LLMTimeoutError (re-raise), LLMError (re-raise), LLMMalformedResponseError (re-raise)
    - Extract first 200 chars as transcript_excerpt
    - Count words for transcript_length_words
    - Ensure all action_items have owner field (set to "unassigned" if not provided by LLM)
    - Call repository.create_summary(summary_dict)
    - Return created summary dict
  - Type hints on all parameters and return values (Principle V)

- [ ] T023 Create `app/api/routes/summaries.py`: HTTP route handlers for POST /api/summaries:
  - **POST /api/summaries** handler:
    - Accept SummaryRequest (transcript: str)
    - Call summarizer.process_transcript() 
    - Catch ValueError (validation) → return 400 with error code (TRANSCRIPT_TOO_SHORT, TRANSCRIPT_TOO_LONG, EMPTY_TRANSCRIPT)
    - Catch LLMTimeoutError → return 503 with error code LLM_TIMEOUT message "Summarization service unavailable; please try again later"
    - Catch LLMError → return 500 with error code PROCESSING_FAILED message "Failed to process transcript; please contact support"
    - Catch LLMMalformedResponseError → return 500 with error code PROCESSING_FAILED message "Failed to process transcript; please contact support"
    - On success → return 201 with SummaryResponse
    - Use error_handler middleware to sanitize all error responses
    - Type hints required on all parameters, return types (Principle V)

- [ ] T024 Update `app/main.py`: Register routes from `app/api/routes/summaries.py`

**Checkpoint: User Story 1 complete and independently testable**

---

## Phase 4: User Story 2 - Retrieve Stored Summary (Priority: P1) 🎯 MVP

**Goal**: User can retrieve a previously stored summary by its ID

**Independent Test**: Retrieve valid summary ID → receive 200 with complete summary object; retrieve invalid ID → receive 404

### Tests for User Story 2 (Required - NFR-002)

- [ ] T025 [P] [US2] Create `tests/unit/test_repository.py`: Test repository pattern (with mocked DB session):
  - `test_create_summary()`: Call create_summary() → stores and returns dict with all fields
  - `test_get_summary_exists()`: Call get_summary(valid_id) → returns dict with all fields
  - `test_get_summary_not_found()`: Call get_summary(invalid_id) → returns None

- [ ] T026 [P] [US2] Create `tests/integration/test_e2e_retrieve.py`: Integration tests with test DB + mocked Bedrock:
  - `test_get_summaries_valid_id()`: GET /api/summaries/{id} with valid ID from prior POST → 200 + summary object with all fields
  - `test_get_summaries_nonexistent_id()`: GET /api/summaries/{uuid4()} → 404 + error code SUMMARY_NOT_FOUND message "Summary not found"
  - `test_get_summaries_invalid_uuid_format()`: GET /api/summaries/invalid-id → 400 + error code INVALID_ID_FORMAT message "Invalid ID format; expected UUID"
  - `test_get_summaries_response_schema()`: 200 response matches api-contract.md schema exactly
  - `test_get_summaries_all_fields_intact()`: Submit → retrieve → all fields unchanged (id, transcript_excerpt, key_points, decisions, action_items with owners, created_at, source)

- [ ] T027 [P] [US2] Create contract tests in `tests/contract/test_api_contract.py`:
  - `test_get_summaries_response_200_schema()`: 200 response must match SummaryResponse schema
  - `test_get_summaries_response_404_schema()`: 404 response must have error, code, timestamp fields
  - `test_get_summaries_response_400_schema()`: 400 response must have error, code, timestamp fields

### Implementation for User Story 2

- [ ] T028 Create `app/api/routes/summaries.py` GET handler:
  - **GET /api/summaries/{id}** handler:
    - Parse path parameter `id` as UUID string
    - Call repository.get_summary(id)
    - If None → return 404 with error code SUMMARY_NOT_FOUND message "Summary not found"
    - If invalid UUID format → return 400 with error code INVALID_ID_FORMAT message "Invalid ID format; expected UUID"
    - On success → return 200 with SummaryResponse
    - Type hints required (Principle V)

**Checkpoint: User Stories 1 & 2 both complete and independently testable**

---

## Phase 5: User Story 3 - Handle LLM Processing Failures (Priority: P1) 🎯 MVP

**Goal**: System gracefully handles LLM failures (timeouts, malformed responses) without storing partial/corrupted data

**Independent Test**: Simulate Bedrock timeout → receive 503; simulate malformed response → receive 500; verify no partial summary stored in either case

### Tests for User Story 3 (Required - NFR-002)

Tests for US3 are already included in Phase 3 (US1) tests but expanded here for clarity:

- [ ] T029 [P] [US3] Add to `tests/integration/test_e2e_submit.py` (already created in T020):
  - Explicit timeout test: `test_post_summaries_bedrock_timeout_no_partial_data()`: Post → mock Bedrock timeout → 503 returned → verify no row exists in DB
  - Explicit malformed test: `test_post_summaries_bedrock_malformed_no_partial_data()`: Post → mock malformed JSON → 500 returned → verify no row exists in DB

- [ ] T030 [P] [US3] Create `tests/unit/test_error_handling.py`: Error path tests:
  - `test_error_handler_strips_api_keys()`: Verify middleware removes AWS keys from error logs
  - `test_error_handler_strips_transcript()`: Verify middleware removes full transcript from error logs
  - `test_error_handler_includes_error_code()`: Verify error response includes error code
  - `test_error_handler_includes_timestamp()`: Verify error response includes ISO 8601 timestamp

### Implementation for User Story 3

- [ ] T031 [P] [US3] Update `app/services/llm_client.py` error handling (explicit per FR-005, FR-006):
  - Add retry logic for LLMTimeoutError (up to 2 retries with exponential backoff if desired)
  - Ensure all exceptions include clear error messages (no stack traces to user)
  - Log errors with sanitized output (error code + request ID, NOT transcript or API keys)

- [ ] T032 [P] [US3] Update `app/services/summarizer.py` to guarantee no partial data stored:
  - Wrap entire process_transcript() in transaction (if using SQLAlchemy session)
  - Catch all LLM exceptions BEFORE calling repository.create_summary()
  - Ensure exception is re-raised to route handler (handler returns 503/500, DB remains clean)

- [ ] T033 Update `app/api/routes/summaries.py` POST handler error responses to match api-contract.md exactly:
  - 503 response: `{ "error": "Summarization service unavailable; please try again later", "code": "LLM_TIMEOUT", "timestamp": "ISO 8601" }`
  - 500 response: `{ "error": "Failed to process transcript; please contact support", "code": "PROCESSING_FAILED", "timestamp": "ISO 8601" }`

**Checkpoint: All user stories 1, 2, 3 complete and independently testable**

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and quality improvements

- [ ] T034 Create database migration/initialization script in `app/storage/init_db.py`: Ensure schema is created on first run
- [ ] T035 [P] Update `requirements.txt` with exact pinned versions (e.g., `fastapi==0.104.1`) after testing
- [ ] T036 Create `README.md` in repository root:
  - Feature overview
  - Quick start: "python -m uvicorn app.main:app --reload"
  - Dependencies: "pip install -r requirements.txt"
  - Environment setup: "cp .env.example .env && export AWS_REGION=us-east-1"
  - Testing: "pytest tests/ -v --cov=app"
  - API docs: "Visit http://localhost:8000/docs"

- [ ] T037 [P] Add logging configuration in `app/main.py`:
  - Configure Python logging to sanitize output (use middleware from T008)
  - Log request IDs (not full transcripts)
  - Log Bedrock errors (not API keys)

- [ ] T038 Run validation against quickstart.md scenarios:
  - Execute Test Scenario 1 (successful submission) from quickstart.md
  - Execute Test Scenario 2 (retrieve stored summary) from quickstart.md
  - Execute Test Scenario 3 (transcript too short) from quickstart.md
  - Execute Test Scenario 4 (transcript too long) from quickstart.md
  - Execute Test Scenario 5 (empty transcript) from quickstart.md
  - Execute Test Scenario 6 (nonexistent ID) from quickstart.md
  - Execute Test Scenario 7 (action items with unassigned owner) from quickstart.md

- [ ] T039 Run full test suite with coverage:
  - Execute: `pytest tests/ -v --cov=app --cov-report=term-missing`
  - Verify 100% coverage for endpoints and services (per NFR-002)
  - Fix any uncovered branches

- [ ] T040 Verify constitution compliance (all 5 principles):
  - Principle I: Verify all Bedrock calls flow through `app/services/llm_client.py` only (no direct boto3 calls elsewhere)
  - Principle II: Verify error responses have NO API keys, credentials, or full transcripts
  - Principle III: Verify explicit exception handling for Bedrock timeout (503), validation error (400), internal error (500)
  - Principle IV: Verify business logic uses repository interface only (no direct SQLAlchemy queries in services)
  - Principle V: Verify all functions have type hints and 100% test coverage for endpoints/services

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — MUST complete before user stories
- **User Stories (Phase 3-5)**: All depend on Foundational completion
  - US1 (Phase 3) can start after Foundational — no dependencies on US2 or US3
  - US2 (Phase 4) can start after Foundational — no dependencies on US1 or US3 (though recommends testing after US1)
  - US3 (Phase 5) tests/errors covered in US1 tests but explicitly validated here
- **Polish (Phase 6)**: Depends on all user stories being complete

### Within Each User Story

**Order within US1**:
1. Write tests first (T016-T021) → FAIL
2. Implement summarizer service (T022)
3. Implement POST route handler (T023-T024)
4. Run tests → PASS

**Order within US2**:
1. Write tests first (T025-T027) → FAIL
2. Implement GET route handler (T028)
3. Run tests → PASS

**Order within US3**:
1. Verify error handling tests from US1 (T029-T030)
2. Update llm_client error handling (T031)
3. Update summarizer transaction handling (T032)
4. Update route error responses (T033)
5. Run tests → PASS

### Parallel Opportunities

- **Setup (Phase 1)**: All [P] tasks (T001-T007) can run in parallel — structure/dependencies independent
- **Foundational (Phase 2)**: Error handling (T008-T009), LLM client (T010), Storage (T011-T013), Models (T014) largely independent — can parallelize strategically:
  - T009 (validation) independent → parallel
  - T010 (llm_client) independent → parallel
  - T011-T013 (storage layer) sequential (interface → repository → sqlite_impl)
  - T014 (models) independent → parallel
  - T015 (main app) depends on all above → run after
- **US1 Tests (Phase 3)**: T016-T021 can run in parallel (different test files, mocked dependencies)
- **US2 Tests (Phase 4)**: T025-T027 can run in parallel
- **US3 Tests (Phase 5)**: T029-T030 can run in parallel

### Suggested MVP Scope

**Minimum Viable Product** = Phases 1-4:
- Phase 1: Setup (T001-T007)
- Phase 2: Foundational (T008-T015)
- Phase 3: User Story 1 - Submit (T016-T024)
- Phase 4: User Story 2 - Retrieve (T025-T028)

This gives users:
- Working POST endpoint that accepts transcripts and returns summaries (US1)
- Working GET endpoint to retrieve stored summaries (US2)
- Comprehensive test coverage
- Constitutional compliance for all 5 principles

**Phase 5+** adds explicit error handling tests and polish, but MVP is functional at Phase 4.

---

## Implementation Strategy & Best Practices

### TDD Approach (Tests First)

1. **For each phase**: Write tests FIRST (T016-T030 for user stories)
2. **Verify tests FAIL** before implementation (tests validate the contract, not the implementation)
3. **Implement code** to make tests pass
4. **Run tests again** → PASS

### Constitutional Compliance Checklist

Before marking a phase complete:

- [ ] **Principle I (LLM Centralization)**: All Bedrock calls go through `llm_client.py`?
- [ ] **Principle II (Security & Privacy)**: Error logs/responses have NO API keys, credentials, full transcripts?
- [ ] **Principle III (Explicit Failure)**: All LLM exceptions explicitly caught and mapped to HTTP codes (503/500)?
- [ ] **Principle IV (Storage Abstraction)**: Business logic uses repository interface only?
- [ ] **Principle V (Code Quality)**: All functions have type hints and 100% test coverage for endpoints/services?

### Database Transactions

- Wrap summarizer.process_transcript() in SQLAlchemy session transaction
- If LLM fails BEFORE repository.create_summary() → exception raised, no DB write, connection rolled back
- If repository.create_summary() fails → exception caught, no partial data persisted

### Error Logging Pattern

```
❌ WRONG: logger.error(f"LLM error: {response} {transcript} {api_key}")
✅ RIGHT: logger.error(f"LLM error for request {request_id}: error_code={code}, will return 503")
```

### Dependency Injection Pattern

```python
# Routes receive dependencies via FastAPI dependency injection
@app.post("/api/summaries")
def post_summaries(
    request: SummaryRequest,
    summarizer_svc: Summarizer = Depends(get_summarizer),
    session: Session = Depends(get_db_session),
):
    # Services and DB session injected automatically
    return summarizer_svc.process_transcript(...)
```

---

## Format Validation Summary

✅ All tasks follow checklist format:
- Checkbox: `- [ ]`
- Task ID: Sequential (T001-T040)
- [P] marker: Included for parallelizable tasks
- [Story] label: Included for US1/US2/US3 phases
- Description: Clear action with exact file path

✅ Total task count: 40 tasks
- Phase 1 (Setup): 7 tasks
- Phase 2 (Foundational): 8 tasks
- Phase 3 (US1): 9 tasks (T016-T024)
- Phase 4 (US2): 4 tasks (T025-T028)
- Phase 5 (US3): 3 tasks (T029-T032) + 1 update (T033)
- Phase 6 (Polish): 7 tasks (T034-T040)

✅ Task count per user story:
- US1: 9 implementation/test tasks (T016-T024)
- US2: 4 implementation/test tasks (T025-T028)
- US3: 4 implementation/test tasks (T029-T033)

✅ Parallel opportunities identified:
- Setup phase: 5 [P] tasks
- Foundational phase: 3 [P] tasks
- US1 tests: 6 [P] tasks
- US2 tests: 3 [P] tasks
- US3 tests: 2 [P] tasks

✅ Independent test criteria for each story:
- **US1**: Submit valid transcript → 201 with all fields; submit invalid → 400 with correct error code
- **US2**: Retrieve by valid ID → 200 with complete data; invalid ID → 404; invalid UUID → 400
- **US3**: LLM timeout → 503 without stored data; LLM error → 500 without stored data; sanitized error responses

✅ MVP scope: Phases 1-4 (Setup + Foundational + US1 + US2) ≈ 28 tasks, fully functional and testable

---

