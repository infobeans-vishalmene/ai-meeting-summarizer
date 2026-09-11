# AI Meeting Notes Summarizer

Generated via Spec-Driven Development.
See specs/001-meeting-summarizer/ for constitution, spec, plan, and tasks.

## Run locally

    pip install -r requirements.txt
    cp .env.example .env
    # Ensure AWS credentials are set (env vars, ~/.aws/credentials, or IAM role)
    uvicorn app.main:app --reload

## Run tests (no AWS calls made -- Bedrock is fully mocked)

    pytest tests/ -v

## Covers

- Phase 2 (Foundational): storage interface + SQLite impl, LLM client, validation, error sanitization
- Phase 3 (US1): submit transcript -> summary
- Phase 4 (US2): retrieve summary by ID
- Phase 5 (US3): explicit LLM timeout/malformed-response handling, no partial writes

Not yet implemented: T029-T031 (Polish phase -- mypy pass, coverage report, manual quickstart).
