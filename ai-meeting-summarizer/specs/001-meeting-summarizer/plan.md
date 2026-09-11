# Implementation Plan: Meeting Notes Summarizer

**Branch**: `001-meeting-summarizer` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-meeting-summarizer/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build an API endpoint that accepts meeting transcripts (50-10,000 words, plain text), processes them through a centralized LLM client to extract key discussion points, decisions, and action items (with explicit owner identification or "unassigned" marking), persists the summary with a unique ID, and provides retrieval by ID. Processing is synchronous with a 60-second timeout. Endpoints are unauthenticated, JSON-only, and include explicit failure handling for all LLM-dependent operations. Storage must use the abstract storage interface to maintain database independence.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: 
- **FastAPI** (API framework with async support)
- **boto3 bedrock-runtime** (AWS Bedrock client for LLM)
- **SQLite** (storage backend via repository pattern)
- **pytest** (testing framework)
- **pydantic** (request/response validation)

**Storage**: SQLite with repository pattern abstraction (enables swapping to PostgreSQL, DynamoDB, etc. without touching business logic per Principle IV)

**LLM Provider**: AWS Bedrock (bedrock-runtime API) using Amazon Nova Lite model (cost-optimized for MVP)

**Testing**: pytest with mocked Bedrock calls (no real AWS API calls in test suite)

**Target Platform**: Web service (RESTful API)

**Project Type**: Web service API

**Performance Goals**: 
- Transcript processing: complete within 60 seconds for 10,000-word input (including Bedrock latency)
- Summary retrieval: <500ms

**Constraints**: 
- No authentication for MVP
- All error logs must sanitize API keys, tokens, and full transcripts (Principle II)
- Synchronous request/response model (no async background jobs for MVP)
- JSON payload format only
- AWS credentials via standard boto3 credential chain (env vars, ~/.aws/config, IAM role, etc.)

**Scale/Scope**: MVP scope (2 endpoints, 3 core user stories, no user auth, no editing, no real-time streaming)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Compliance Plan | Status |
|-----------|-------------|-----------------|--------|
| **I. LLM Client Centralization** | All LLM calls through single centralized module | Create LLM orchestrator service; all transcript processing routed through it; no direct provider imports | ✅ PLANNED |
| **II. Security & Privacy** | No API keys, tokens, or full transcripts in logs/errors | Implement error sanitization layer; use request IDs instead of full content in logs | ✅ PLANNED |
| **III. Explicit Failure Handling** | Every LLM-dependent function handles timeouts and malformed responses explicitly | Implement LLM client wrapper with explicit exception handling; test timeout and malformed-response scenarios | ✅ PLANNED |
| **IV. Storage Abstraction** | Business logic independent of storage implementation | Use storage interface only; define clear contracts for CRUD operations; no DB-specific queries in service logic | ✅ PLANNED |
| **V. Code Quality Standards** | Type hints on all functions; tests for all endpoints/logic | Enforce type hints in function signatures; 100% test coverage for endpoint handlers and service layer | ✅ PLANNED |

**GATE STATUS**: ✅ PASS — All constitution principles can be satisfied within MVP scope. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-meeting-summarizer/
├── spec.md              # Feature specification (clarified)
├── plan.md              # This file (Phase 1 design planning)
├── research.md          # Phase 0 research findings (minimal; all decisions clarified)
├── data-model.md        # Phase 1 output: Summary entity definition
├── quickstart.md        # Phase 1 output: Validation/test scenarios
├── contracts/           # Phase 1 output: API contract definitions
│   └── api-contract.md  # OpenAPI-style endpoint specifications
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
# FastAPI application structure (SELECTED)

app/
├── __init__.py
├── main.py                           # FastAPI app entry point; route definitions
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       └── summaries.py              # POST/GET /api/summaries handlers
├── services/
│   ├── __init__.py
│   ├── summarizer.py                 # Core orchestration: validation → LLM → storage
│   └── llm_client.py                 # Bedrock wrapper; centralized LLM interface (Principle I)
├── storage/
│   ├── __init__.py
│   ├── interface.py                  # Abstract storage interface (Principle IV)
│   ├── repository.py                 # Repository pattern implementation
│   └── sqlite_impl.py                # SQLite-specific implementation
├── models/
│   ├── __init__.py
│   └── summary.py                    # Pydantic models + SQLAlchemy ORM for Summary entity
├── middleware/
│   ├── __init__.py
│   └── error_handler.py              # Error sanitization (no keys/transcripts in logs; Principle II)
└── utils/
    ├── __init__.py
    └── validation.py                 # Input validation (word count, length checks)

tests/
├── __init__.py
├── conftest.py                       # pytest fixtures (mocked Bedrock client, test DB)
├── unit/
│   ├── __init__.py
│   ├── test_summarizer.py            # Service layer tests (mocked LLM & storage)
│   ├── test_llm_client.py            # LLM client wrapper tests (mocked Bedrock)
│   └── test_validation.py            # Input validation tests
├── integration/
│   ├── __init__.py
│   ├── test_e2e_submit.py            # End-to-end: POST /api/summaries (with test DB)
│   └── test_e2e_retrieve.py          # End-to-end: GET /api/summaries/{id} (with test DB)
└── contract/
    ├── __init__.py
    └── test_api_contract.py          # API response schema validation

requirements.txt                      # Python dependencies
.env.example                          # Example AWS credentials config
sqlite.db                             # SQLite database file (git-ignored)
```

**Structure Decision**: Standard FastAPI application structure with clear separation of concerns:
- **app/api/routes/**: HTTP layer (request/response handling)
- **app/services/**: Business logic (orchestration, LLM calls, validation)
- **app/storage/**: Data access layer (repository pattern with abstract interface)
- **app/models/**: Data models (Pydantic for API validation, SQLAlchemy ORM for DB)
- **app/middleware/**: Cross-cutting concerns (error sanitization per Principle II)
- **tests/**: Unit, integration, and contract tests with full Bedrock mocking

**Bedrock Integration**: All Bedrock API calls flow through single `llm_client.py` module exposing a clean `summarize(transcript: str) -> dict` interface. Model/provider changes require only this module; no coupling in business logic.

## Complexity Tracking

No constitutional violations identified. All 5 core principles can be satisfied within the proposed architecture:

| Principle | Implementation Strategy | Risk Assessment |
|-----------|------------------------|-----------------|
| I. LLM Centralization | Dedicated `llm_client.py` module wraps all Bedrock API calls; business logic routes through this module only | ✅ Low — straightforward wrapper pattern |
| II. Security & Privacy | `error_handler.py` middleware sanitizes logs/errors; boto3 credentials via credential chain (never hardcoded) | ✅ Low — standard log filtering + AWS best practices |
| III. Failure Handling | Explicit exception handling in llm_client.py for Bedrock timeouts + malformed responses; propagated as 503/500 | ✅ Low — defensive programming standard |
| IV. Storage Abstraction | `storage/interface.py` defines CRUD contract; business logic accesses only via repository; SQLite/PostgreSQL swappable | ✅ Low — interface pattern well-established; repository pattern isolates DB |
| V. Code Quality | All functions require type hints; pytest coverage target 100% for endpoints/services; Pydantic validates API schemas | ✅ Low — FastAPI + pytest enforce standards |

**AWS Bedrock Integration Risks** (mitigated by technology choices):
- **Model Availability**: Amazon Nova Lite available in standard AWS regions; fallback/upgrade path to Nova Pro if accuracy issues
- **Timeout Handling**: boto3 client timeout set to 50s (leaving 10s margin before 60s endpoint timeout); explicit retry logic in llm_client.py
- **Bedrock Error Codes**: ThrottlingException → 503; ValidationException/InternalServerException → 500; structured handling per Principle III
- **Testing**: All Bedrock calls mocked in pytest (no real AWS charges); conftest.py provides mock fixtures

**SQLite + Repository Pattern** (mitigated by storage abstraction):
- **File-Based Storage**: Fine for MVP; migration to PostgreSQL via repository pattern swap-out (no business logic changes)
- **Concurrency**: Row-level locking sufficient for MVP; scales to PostgreSQL as needed
- **Migrations**: SQLAlchemy Alembic can manage schema evolution; not required for initial MVP

**No Unresolved Design Questions**: All key decisions finalized in clarifications phase. Implementation can proceed directly to Phase 2 task generation.

---

## Technology Stack Details

### API Framework: FastAPI

**Selection Rationale**:
- ✅ Native async/await support (future scaling; synchronous routes work fine for MVP)
- ✅ Built-in Pydantic integration for automatic request/response validation and JSON serialization
- ✅ Automatic OpenAPI documentation (aligns with our contract-first approach)
- ✅ Excellent error handling middleware support (Principle II error sanitization)

**Implementation Pattern**:
- Routes defined in `app/api/routes/summaries.py` using dependency injection for services
- Pydantic models in `app/models/summary.py` for request/response schemas
- Middleware for error handling/logging in `app/middleware/error_handler.py`

### LLM Provider: AWS Bedrock (Amazon Nova Lite)

**Selection Rationale**:
- ✅ Cost-optimized for MVP (Nova Lite significantly cheaper than GPT-4, Claude 3)
- ✅ Structured output support (configure to return JSON with consistent schema)
- ✅ No additional API key management (uses AWS IAM credentials via boto3 credential chain)
- ✅ Regional availability in standard AWS regions (us-east-1, us-west-2, eu-west-1, etc.)

**Invocation Pattern** (`app/services/llm_client.py`):
```python
# Pseudo-code structure
def summarize(transcript: str) -> dict:
    """
    Invoke Bedrock InvokeModel API with Amazon Nova Lite
    Args:
        transcript: raw meeting transcript (50-10,000 words)
    Returns:
        dict with keys: key_points, decisions, action_items
    Raises:
        LLMTimeoutError: if request exceeds 50s
        LLMError: if response is malformed or API error occurs
    """
```

**Error Handling Mapping**:
- `botocore.exceptions.ReadTimeoutError` → 503 Service Unavailable (per FR-005)
- `botocore.exceptions.ClientError` (ThrottlingException) → 503 Service Unavailable
- `botocore.exceptions.ClientError` (ValidationException) → 500 Internal Server Error
- `botocore.exceptions.ClientError` (InternalServerException) → 500 Internal Server Error
- Malformed JSON response (parsing fails) → 500 Internal Server Error (per FR-006)

**Configuration**:
- AWS credentials: Standard boto3 credential chain (env vars → ~/.aws/credentials → IAM role)
- Region: Inferred from `AWS_REGION` env var or default region in ~/.aws/config
- Client timeout: 50s (leaving 10s margin before endpoint 60s timeout)
- Model ID: `amazon.nova-lite-v1:0`

**Testing**:
- Use `unittest.mock.patch('app.services.llm_client.boto3.client')` to mock Bedrock calls
- Mock response structure matches Nova Lite output format (JSON with key_points, decisions, action_items arrays)

### Storage: SQLite + Repository Pattern

**Selection Rationale**:
- ✅ File-based; no external database dependency for MVP
- ✅ Repository pattern abstraction (Principle IV) enables swapping to PostgreSQL/DynamoDB later
- ✅ SQLAlchemy ORM provides SQL generation and connection pooling
- ✅ pytest integration with in-memory SQLite (`:memory:`) for fast test execution

**Architecture**:

```
Business Logic (summarizer.py)
        ↓
Repository Interface (storage/interface.py)
        ↓
Repository Impl (storage/repository.py)
        ↓
SQLAlchemy ORM (models/summary.py)
        ↓
SQLite (sqlite.db)
```

**Interface Contract** (`app/storage/interface.py`):
```python
# Pseudo-code
class StorageInterface:
    def create_summary(self, summary: Summary) -> str:
        """Create summary; return UUID string"""
        
    def get_summary(self, summary_id: str) -> Optional[Summary]:
        """Retrieve summary by UUID; return None if not found"""
```

**SQLite Schema** (`app/storage/sqlite_impl.py`):
- Table: `summaries`
  - Columns: id (UUID primary key), transcript_excerpt (TEXT), transcript_length_words (INTEGER), key_points (JSON), decisions (JSON), action_items (JSON), created_at (TIMESTAMP)
- Uses SQLAlchemy Declarative model for ORM mapping

**Testing**:
- Integration tests use SQLite `:memory:` database
- `conftest.py` provides pytest fixture that creates in-memory DB and yields clean session per test
- No external database required for CI/CD

### Testing Framework: pytest + Mocks

**Selection Rationale**:
- ✅ Industry standard for Python; excellent fixture system for setup/teardown
- ✅ `unittest.mock` built into Python stdlib (no additional dependencies for mocking)
- ✅ Parametrized tests reduce boilerplate
- ✅ Integration with FastAPI TestClient for endpoint testing

**Test Organization**:

| Test Type | Location | Scope | Mocking |
|-----------|----------|-------|---------|
| **Unit** | `tests/unit/` | Individual functions (validation, service methods) | Mock LLM, storage |
| **Integration** | `tests/integration/` | End-to-end POST/GET with test DB | Mock Bedrock, real SQLite `:memory:` |
| **Contract** | `tests/contract/` | Response schema validation against api-contract.md | Mock Bedrock, real SQLite `:memory:` |

**Mocking Strategy**:
```python
# Example in conftest.py
@pytest.fixture
def mock_bedrock():
    with patch('app.services.llm_client.boto3.client') as mock_client:
        mock_instance = MagicMock()
        mock_instance.invoke_model.return_value = {
            'body': BytesIO(json.dumps({
                'key_points': [...],
                'decisions': [...],
                'action_items': [...]
            }).encode())
        }
        mock_client.return_value = mock_instance
        yield mock_instance
```

### Dependencies: requirements.txt

```
fastapi==0.104.1
uvicorn==0.24.0
boto3==1.34.0
sqlalchemy==2.0.23
pydantic==2.5.0
pytest==7.4.3
pytest-cov==4.1.0
python-dotenv==1.0.0
```

**Notes**:
- `python-dotenv`: Load `.env` for AWS_REGION and other config (not secrets — use credential chain)
- `pytest-cov`: Coverage reporting (target 100% for endpoints/services)
- `sqlalchemy`: ORM for database abstraction

### Credentials & Configuration

**AWS Credentials** (no hardcoding):
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (optional)
- AWS credential file: `~/.aws/credentials` (recommended for local development)
- IAM Role: When deployed to EC2/ECS/Lambda, boto3 uses role credentials automatically
- `.env.example` provides template (for reference only; actual credentials never committed)

**Application Configuration**:
- `AWS_REGION`: Environment variable (default: `us-east-1`)
- Database path: `sqlite.db` (file-based, git-ignored)
- LLM timeout: 50s (hardcoded in llm_client.py)
- Endpoint timeout: 60s (hardcoded in routes/summaries.py)

---

## Next Phase: Task Generation

Execute `/speckit-tasks` to generate `tasks.md` with actionable, dependency-ordered implementation tasks. Expected output will cover:
1. Project setup (dependencies, .env template, database schema)
2. Storage layer (interface + SQLite implementation)
3. LLM client (Bedrock wrapper with error handling)
4. Service layer (summarizer orchestration + validation)
5. API routes (POST/GET handlers with middleware)
6. Testing (unit, integration, contract test suites)
7. Validation (quickstart scenarios, constitutional checks)
