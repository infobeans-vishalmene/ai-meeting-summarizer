"""
Summary entity: Pydantic models (API validation) + SQLAlchemy ORM (persistence).

Per spec.md "Key Entities" section.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ---------------------------------------------------------------------------
# API request/response schemas (Pydantic) — per spec.md API Request/Response Examples
# ---------------------------------------------------------------------------

class ActionItem(BaseModel):
    """A single action item extracted from a transcript. Per FR-008."""
    description: str
    owner: str = Field(
        description='Name of assigned person, or "unassigned" if not '
        'clearly stated in the transcript (never guessed/inferred).'
    )
    priority: Optional[str] = Field(
        default=None, description='"high" | "medium" | "low", omitted if not stated'
    )


class SummarizeRequest(BaseModel):
    """Request body for POST /api/summaries. Per FR-001."""
    transcript: str


class SummaryResponse(BaseModel):
    """Response body for POST /api/summaries and GET /api/summaries/{id}."""
    id: str
    transcript_excerpt: str
    transcript_length_words: int
    key_points: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    created_at: datetime

    class Config:
        from_attributes = True  # allows building directly from the ORM object


# ---------------------------------------------------------------------------
# ORM model (SQLAlchemy) — per plan.md SQLite Schema
# ---------------------------------------------------------------------------

class SummaryORM(Base):
    __tablename__ = "summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_excerpt = Column(String, nullable=False)
    transcript_length_words = Column(Integer, nullable=False)
    key_points = Column(JSON, nullable=False)
    decisions = Column(JSON, nullable=False)
    action_items = Column(JSON, nullable=False)  # list[dict] matching ActionItem shape
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def build_summary_response(orm_obj: SummaryORM) -> SummaryResponse:
    """Convert an ORM row into the API response schema."""
    return SummaryResponse(
        id=orm_obj.id,
        transcript_excerpt=orm_obj.transcript_excerpt,
        transcript_length_words=orm_obj.transcript_length_words,
        key_points=orm_obj.key_points,
        decisions=orm_obj.decisions,
        action_items=[ActionItem(**item) for item in orm_obj.action_items],
        created_at=orm_obj.created_at,
    )
