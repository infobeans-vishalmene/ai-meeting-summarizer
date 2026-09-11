"""
API routes for /api/summaries.

Error mapping (per plan.md):
- ValidationError            -> 400
- LLMTimeoutError             -> 503
- LLMError                    -> 500
- summary not found (GET)     -> 404
"""
from fastapi import APIRouter, Depends, HTTPException

from app.middleware.error_handler import log_error
from app.models.summary import SummarizeRequest, SummaryResponse, build_summary_response
from app.services import summarizer
from app.services.summarizer import LLMError, LLMTimeoutError
from app.storage.interface import StorageInterface
from app.utils.validation import ValidationError

router = APIRouter()


def get_storage() -> StorageInterface:
    """Overridden in main.py with a real singleton; overridden in tests with a mock."""
    raise NotImplementedError("Storage dependency not configured")


@router.post("/api/summaries", response_model=SummaryResponse, status_code=201)
def submit_transcript(
    request: SummarizeRequest, storage: StorageInterface = Depends(get_storage)
) -> SummaryResponse:
    try:
        summary = summarizer.create_summary(request.transcript, storage)
        return build_summary_response(summary)

    except ValidationError as exc:
        # Per FR-002/003/015 — exact user-facing messages, no internals to sanitize.
        raise HTTPException(status_code=400, detail=exc.message)

    except LLMTimeoutError as exc:
        request_id = log_error("submit_transcript.llm_timeout", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Summarization service unavailable; please try again later "
            f"(ref: {request_id})",
        )

    except LLMError as exc:
        request_id = log_error("submit_transcript.llm_error", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process transcript; please contact support "
            f"(ref: {request_id})",
        )


@router.get("/api/summaries/{summary_id}", response_model=SummaryResponse)
def retrieve_summary(
    summary_id: str, storage: StorageInterface = Depends(get_storage)
) -> SummaryResponse:
    summary = summarizer.get_summary(summary_id, storage)
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return build_summary_response(summary)
