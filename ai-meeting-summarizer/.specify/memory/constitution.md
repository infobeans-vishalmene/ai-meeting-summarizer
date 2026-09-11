<!-- SYNC IMPACT REPORT
This document was created/amended by speckit-constitution.

VERSION CHANGE: Template → 1.0.0 (Initial Constitution)
RATIONALE: First official constitution for AI Meeting Summarizer project
CREATION_DATE: 2026-09-11

NEW SECTIONS ADDED:
- Core Principles (5 principles established)
- Governance section

MODIFIED SECTIONS: None (initial creation)
REMOVED SECTIONS: None

TODO ITEMS: None - all placeholders resolved with project-specific values
-->

# AI Meeting Summarizer Constitution

## Core Principles

### I. LLM Client Centralization

All LLM API interactions must be routed through a single, centralized client module. Direct API calls scattered across the codebase are strictly prohibited. This ensures:
- Consistent token management and rate limiting across the application
- Unified request/response logging and monitoring
- Centralized error handling and retry logic
- Simplified API key rotation and credential management
- Single source of truth for LLM provider configuration

**Non-Negotiable**: New features must never introduce direct LLM provider imports or API calls. All interactions MUST go through the designated LLM client module.

### II. Security & Privacy First

API keys and sensitive credentials must never be logged, persisted in error messages, or included in stack traces. Full transcripts must not be stored in logs or error reports. This is a critical security requirement:
- Environment variables and secure vaults are the only acceptable credential storage
- Error handling must sanitize all output to exclude API keys, tokens, and full conversation histories
- Logs must include only essential context (request IDs, operation types) without sensitive data
- Code reviews must explicitly verify compliance with this principle

**Non-Negotiable**: Any code that logs or persists API keys, authentication tokens, or full transcripts will be rejected.

### III. Explicit Failure Handling

Every function that depends on LLM calls must explicitly handle failure modes. Silent failures, timeouts, or malformed responses are unacceptable:
- Network timeouts MUST be caught and handled with user-facing error messages and fallback strategies
- Malformed or unexpected API responses MUST be validated and rejected explicitly
- Rate limiting responses MUST trigger appropriate backoff or graceful degradation
- All failure paths must be tested and documented
- Functions must never assume API success; defensive programming is mandatory

**Non-Negotiable**: Functions that depend on LLM calls must have explicit error handling with tests covering timeout and malformed-response scenarios.

### IV. Storage Abstraction

Business logic must remain independent of the storage implementation. The storage layer must be swappable without requiring changes to application logic:
- Database-specific queries and assumptions are forbidden in business logic
- All data access must be routed through a well-defined storage interface
- The storage layer must support multiple backends (SQL, NoSQL, cloud, etc.) through a consistent contract
- Tests must not depend on a specific database implementation
- Migrations and schema changes must be decoupled from business logic

**Non-Negotiable**: Storage implementations must be pluggable. No feature can assume a specific database technology.

### V. Code Quality Standards

Code must meet strict quality standards to ensure maintainability and reliability:
- **Type Hints**: All functions must include complete type hints for parameters and return values
- **Tests**: All endpoints and business logic must have corresponding test coverage
- **Documentation**: Functions must include docstrings explaining purpose, parameters, and exceptions
- **Backwards Compatibility**: Breaking changes require explicit justification and a migration plan

**Non-Negotiable**: Pull requests without type hints on all functions or missing endpoint/logic tests will not be merged.

## Governance

This constitution establishes binding principles for all development in the AI Meeting Summarizer project. All team members, contributors, and automated systems must comply with these principles.

**Amendment Process**: Constitutional changes require:
1. Clear rationale document explaining the change
2. Impact assessment on existing code
3. Team consensus or documented approval
4. Updated version number following semantic versioning
5. Commit message including amendment date and rationale

**Compliance Verification**: 
- Code reviews must verify principle compliance before merge
- Violations must be addressed before PR acceptance
- Principles supersede all other development guidelines

**Versioning Policy**:
- MAJOR version: Backward-incompatible principle removals or redefinitions
- MINOR version: New principles added or materially expanded guidance
- PATCH version: Clarifications, wording corrections, or non-semantic refinements

**Version**: 1.0.0 | **Ratified**: 2026-09-11 | **Last Amended**: 2026-09-11
