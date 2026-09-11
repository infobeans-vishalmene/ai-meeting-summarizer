"""
Abstract storage interface — Constitution Principle IV:
"Business logic must remain independent of the storage implementation."

Business logic (summarizer.py) depends ONLY on this interface, never on
SQLite, SQLAlchemy, or any other storage detail directly.
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.models.summary import SummaryORM


class StorageInterface(ABC):
    @abstractmethod
    def create_summary(self, summary: SummaryORM) -> str:
        """Persist a summary. Returns the summary's unique ID."""
        raise NotImplementedError

    @abstractmethod
    def get_summary(self, summary_id: str) -> Optional[SummaryORM]:
        """Retrieve a summary by ID. Returns None if it doesn't exist. Per FR-013."""
        raise NotImplementedError
