"""
Error sanitization — Constitution Principle II:
"API keys and sensitive credentials must never be logged, persisted in
error messages, or included in stack traces. Full transcripts must not be
stored in logs or error reports."

Usage: call log_error(...) instead of logging exceptions directly. It never
accepts or logs raw transcript text or credential-shaped values — only a
short operation label and an optional request ID.
"""
import logging
import uuid

logger = logging.getLogger("meeting_summarizer")


def log_error(operation: str, exc: Exception, request_id: str | None = None) -> str:
    """
    Logs an error with only safe, non-sensitive context.

    Returns the request_id used (generated if not provided) so it can be
    surfaced to the client for support correlation, without ever exposing
    internals.
    """
    request_id = request_id or str(uuid.uuid4())
    # Deliberately log only: request_id, operation name, exception type.
    # Never log exc's full message/args, since upstream errors (e.g. Bedrock
    # ClientError) can echo request payload content.
    logger.error(
        "operation=%s request_id=%s error_type=%s",
        operation,
        request_id,
        type(exc).__name__,
    )
    return request_id
