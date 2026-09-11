"""
Summarizer service: orchestrates validation -> LLM client -> storage.

This is the only place business logic lives. Routes stay thin; storage and
LLM client stay swappable (Constitution Principles I and IV).
"""
from app.models.summary import SummaryORM
from app.services import llm_client
from app.storage.interface import StorageInterface
from app.utils.validation import validate_transcript, ValidationError

# re-exported so routes can catch these without importing llm_client directly
LLMTimeoutError = llm_client.LLMTimeoutError
LLMError = llm_client.LLMError


def create_summary(transcript: str, storage: StorageInterface) -> SummaryORM:
    """
    Full submit flow: validate -> summarize via LLM -> persist.

    Raises:
        ValidationError: transcript fails validation rules (caller -> 400)
        LLMTimeoutError: LLM call timed out/throttled (caller -> 503)
        LLMError: LLM call failed or returned malformed data (caller -> 500)

    Per spec.md Acceptance Scenario (US3-3): if the LLM step raises, nothing
    is persisted — storage.create_summary() is only reached after a
    successful, validated LLM response.
    """
    word_count = validate_transcript(transcript)  # raises ValidationError

    result = llm_client.summarize(transcript)  # raises LLMTimeoutError / LLMError

    summary = SummaryORM(
        transcript_excerpt=transcript[:200],
        transcript_length_words=word_count,
        key_points=result["key_points"],
        decisions=result["decisions"],
        action_items=result["action_items"],
    )
    storage.create_summary(summary)
    return summary


def get_summary(summary_id: str, storage: StorageInterface) -> SummaryORM | None:
    """Retrieve flow: pure passthrough to storage. Returns None if not found."""
    return storage.get_summary(summary_id)
