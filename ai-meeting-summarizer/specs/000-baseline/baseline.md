# Baseline: Meeting Notes Summarizer (as of feature 001)

**Purpose**: Ground truth of what currently exists in the codebase, derived
by reading the implementation — not from spec.md/plan.md (which describe
intent; this describes reality). Future feature specs are checked against
this file, not against memory of what "should" be there.

## Existing Endpoints

- `POST /api/summaries` — accepts `{transcript: str}`, returns 201 with a
  `SummaryResponse` (id, transcript_excerpt, transcript_length_words,
  key_points, decisions, action_items, created_at). Errors: 400 (validation),
  503 (LLM timeout), 500 (LLM error).
- `GET /api/summaries/{id}` — returns 200 with `SummaryResponse`, or 404.
- `GET /health` — liveness check, returns `{status: "ok"}`.

## Existing Abstractions (new features MUST reuse these, not reimplement)

- **`app/services/llm_client.py`** — the ONLY module permitted to call
  Bedrock. Exposes `summarize(transcript: str) -> dict`, raising
  `LLMTimeoutError` or `LLMError`. Uses Nova Lite (`amazon.nova-lite-v1:0`).
  A new feature needing an LLM call must add a function here, or call
  through here — never import boto3 directly elsewhere.
- **`app/storage/interface.py`** (`StorageInterface`) — abstract contract
  with `create_summary()` / `get_summary()`. Implemented by
  `SQLiteRepository` in `app/storage/sqlite_impl.py`. A new feature needing
  persistence extends this interface (or adds a sibling interface following
  the same pattern), never queries SQLite directly.
- **`app/middleware/error_handler.py`** (`log_error()`) — the only sanctioned
  way to log a failure; strips transcript content and credentials by
  construction (accepts only `operation: str`, `exc: Exception`,
  optional `request_id`).
- **`app/utils/validation.py`** — word-count validation constants
  (`MIN_WORDS = 50`, `MAX_WORDS = 10_000`) and `ValidationError`.

## Existing Data Shape

`SummaryORM` (`app/models/summary.py`), persisted fields:
`id, transcript_excerpt, transcript_length_words, key_points (JSON list),
decisions (JSON list), action_items (JSON list of {description, owner,
priority?}), created_at`.

**Relevant existing behavior for the next feature**: `action_items[].owner`
is already set to the literal string `"unassigned"` at generation time
(in `llm_client.py`'s prompt contract) when no owner is stated. This value
is stored as-is — there is currently no separate flag, count, or query
surface for unassigned items; a caller must fetch a full summary and scan
the array client-side to find them.

## Constitution Constraints Already In Force

(Full text: `.specify/memory/constitution.md`, v1.0.0)

- Principle I: centralized LLM client — confirmed followed (`llm_client.py`
  is the sole Bedrock caller).
- Principle II: no secrets/transcripts in logs — confirmed followed
  (`error_handler.py` only accepts operation name + exception type).
- Principle III: explicit LLM failure handling — confirmed followed
  (`LLMTimeoutError`/`LLMError` mapped to 503/500 in routes).
- Principle IV: storage abstraction — confirmed followed (routes/services
  depend on `StorageInterface`, never on `SQLiteRepository` directly).
- Principle V: type hints + test coverage — confirmed followed; 15/15 tests
  passing as of this baseline.

## Known Gaps (not violations — just not built yet)

- No endpoint to list/filter summaries (spec.md 001 explicitly marks this
  out of scope).
- No update/edit of an existing summary after creation (also out of scope
  per spec.md 001).
- `SummaryORM.action_items` is untyped JSON at the DB layer — no schema
  enforcement below the Pydantic API boundary.
