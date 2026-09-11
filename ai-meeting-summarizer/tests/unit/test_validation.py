import pytest

from app.utils.validation import validate_transcript, ValidationError


def test_valid_transcript_returns_word_count():
    transcript = " ".join(["word"] * 60)
    assert validate_transcript(transcript) == 60


def test_empty_transcript_rejected():
    with pytest.raises(ValidationError, match="Transcript cannot be empty"):
        validate_transcript("")


def test_whitespace_only_transcript_rejected():
    with pytest.raises(ValidationError, match="Transcript cannot be empty"):
        validate_transcript("   \n\t  ")


def test_below_minimum_words_rejected():
    transcript = " ".join(["word"] * 49)
    with pytest.raises(ValidationError, match="at least 50 words"):
        validate_transcript(transcript)


def test_above_maximum_words_rejected():
    transcript = " ".join(["word"] * 10_001)
    with pytest.raises(ValidationError, match="exceeds maximum length"):
        validate_transcript(transcript)


def test_exact_boundaries_are_valid():
    assert validate_transcript(" ".join(["word"] * 50)) == 50
    assert validate_transcript(" ".join(["word"] * 10_000)) == 10_000
