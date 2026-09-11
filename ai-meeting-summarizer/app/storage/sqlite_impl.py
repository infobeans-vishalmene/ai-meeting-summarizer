"""
SQLite implementation of StorageInterface.

Swapping to PostgreSQL/DynamoDB later means writing a new class here that
implements StorageInterface — summarizer.py and the routes never change.
Per Constitution Principle IV.
"""
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.summary import Base, SummaryORM
from app.storage.interface import StorageInterface


class SQLiteRepository(StorageInterface):
    def __init__(self, db_path: str = "sqlite.db"):
        # check_same_thread=False is safe here because FastAPI's default sync
        # route handling uses a thread per request, and each request gets its
        # own session via _session_factory().
        self._engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _session(self) -> Session:
        return self._session_factory()

    def create_summary(self, summary: SummaryORM) -> str:
        with self._session() as session:
            session.add(summary)
            session.commit()
            session.refresh(summary)
            return summary.id

    def get_summary(self, summary_id: str) -> Optional[SummaryORM]:
        with self._session() as session:
            return session.get(SummaryORM, summary_id)
