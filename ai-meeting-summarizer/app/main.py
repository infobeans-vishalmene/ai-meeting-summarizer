"""FastAPI application entry point."""
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import summaries
from app.storage.sqlite_impl import SQLiteRepository

load_dotenv()

app = FastAPI(title="Meeting Notes Summarizer", version="0.1.0")

_storage = SQLiteRepository(db_path=os.environ.get("DATABASE_PATH", "sqlite.db"))


def get_storage_override() -> SQLiteRepository:
    return _storage


app.dependency_overrides[summaries.get_storage] = get_storage_override
app.include_router(summaries.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
