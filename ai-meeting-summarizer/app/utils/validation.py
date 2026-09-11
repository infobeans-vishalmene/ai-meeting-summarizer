"""
Transcript input validation.

Per spec.md:
- FR-002: reject transcripts over 10,000 words
- FR-003: reject empty/whitespace-only transcripts
- FR-015: reject transcripts under 50 words
"""

MIN_WORDS = 50
MAX_WORDS = 10_000


class ValidationError(Exception):
    """Raised when a transcript fails validation. Carries a user-facing message."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_transcript(transcript: str) -> int:
    """
    Validates a transcript per spec.md rules.

    Returns the word count if valid.
    Raises ValidationError with the exact spec.md message otherwise.
    """
    if not transcript or not transcript.strip():
        raise ValidationError("Transcript cannot be empty")

    word_count = len(transcript.split())

    if word_count < MIN_WORDS:
        raise ValidationError("Transcript must contain at least 50 words")

    if word_count > MAX_WORDS:
        raise ValidationError("Transcript exceeds maximum length of 10,000 words")

    return word_count
