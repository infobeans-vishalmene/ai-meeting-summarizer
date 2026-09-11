# Data Model: Meeting Notes Summarizer

**Date**: 2026-09-11  
**Phase**: Phase 1 (Design)

## Entity: Summary

The `Summary` entity represents a processed meeting transcript with extracted insights, decisions, and action items.

### Fields

| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | UUID (string) | PRIMARY KEY, NOT NULL | Unique identifier; generated on creation (UUID v4) |
| `transcript_excerpt` | String | Max 200 chars, NOT NULL | First 200 characters of the original transcript for context |
| `transcript_length_words` | Integer | ≥ 50, ≤ 10,000, NOT NULL | Word count of the original transcript |
| `key_points` | Array of strings | NOT NULL, default: `[]` | Extracted key discussion points; ordered by significance |
| `decisions` | Array of strings | NOT NULL, default: `[]` | Decisions made during the meeting; one per array element |
| `action_items` | Array of ActionItem | NOT NULL, default: `[]` | List of action items with owners and optional priority |
| `created_at` | ISO 8601 timestamp | NOT NULL, auto-set | Server timestamp when summary was generated (UTC) |
| `source` | Enum: "api" | NOT NULL, default: "api" | Source of the summary (MVP only supports API) |

### Nested Entity: ActionItem

| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `description` | String | 1-500 chars, NOT NULL | What needs to be done |
| `owner` | String | 1-100 chars, NOT NULL | Name of assigned person or "unassigned" if not clearly stated |
| `priority` | Enum: "high" \| "medium" \| "low" | OPTIONAL, nullable | Priority level if determinable from transcript; omit if not stated |

### Validation Rules

1. **Word Count**: `transcript_length_words` MUST be between 50 and 10,000 (inclusive)
   - Transcripts <50 words are rejected at API layer (FR-015)
   - Transcripts >10,000 words are rejected at API layer (FR-002)

2. **Non-Empty**: 
   - `key_points`, `decisions`, `action_items` must be arrays (may be empty, but array type)
   - At least one of these three SHOULD contain data for meaningful summary (recommend validation in service layer)

3. **Owner Attribution**:
   - `action_items[].owner` must be set to "unassigned" if no clear owner mentioned in transcript
   - Never leave owner field null or omit it; always provide a string value
   - No guessing or inference; explicit mention in transcript only (per Assumption 4 in spec)

4. **Timestamp Format**: `created_at` must be ISO 8601 format with UTC timezone (e.g., `2026-09-11T14:32:00Z`)

5. **Uniqueness**: No uniqueness constraint on `transcript_excerpt` or content; identical transcripts generate separate summaries (per Assumption 5 in spec)

### Lifecycle

```
Created: Summary persisted immediately after successful LLM processing
Stored: Summary retrievable by ID indefinitely (Assumption 6)
Updated: NOT SUPPORTED in MVP (out of scope per spec)
Deleted: NOT SUPPORTED in MVP (future enhancement)
```

### Storage Interface Contract

The `Summary` entity interacts with storage layer through abstract interface (Principle IV):

```python
# Pseudo-interface (actual implementation in separate interface.py)

class StorageInterface:
    async def create_summary(summary: Summary) -> Summary:
        """Create and persist a new summary; return with ID assigned"""
        
    async def get_summary(id: UUID) -> Summary | None:
        """Retrieve summary by ID; return None if not found"""
        
    # Optional for MVP (no delete in scope):
    # async def delete_summary(id: UUID) -> bool:
```

### Implementation: SQLAlchemy ORM + SQLite

**File**: `app/models/summary.py`

```python
# Pseudo-code showing structure (actual implementation in separate file)

from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime

Base = declarative_base()

# SQLAlchemy ORM Model (database mapping)
class SummaryORM(Base):
    __tablename__ = "summaries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    transcript_excerpt = Column(String(200), nullable=False)
    transcript_length_words = Column(Integer, nullable=False)
    key_points = Column(JSON, nullable=False, default=[])
    decisions = Column(JSON, nullable=False, default=[])
    action_items = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source = Column(String(50), nullable=False, default="api")

# Pydantic Request/Response Model (API validation)
class SummaryRequest(BaseModel):
    transcript: str

class ActionItemResponse(BaseModel):
    description: str
    owner: str
    priority: Optional[str] = None

class SummaryResponse(BaseModel):
    id: str
    transcript_excerpt: str
    transcript_length_words: int
    key_points: List[str]
    decisions: List[str]
    action_items: List[ActionItemResponse]
    created_at: str
    source: str
```

**Repository Pattern**: `app/storage/repository.py`

```python
# Pseudo-code showing pattern (actual implementation in separate file)

class SummaryRepository:
    """Abstracts storage implementation; business logic uses only this"""
    
    def __init__(self, session):
        self.session = session
    
    def create(self, summary_data: dict) -> str:
        """Create summary; return UUID string"""
        orm_obj = SummaryORM(**summary_data)
        self.session.add(orm_obj)
        self.session.commit()
        return orm_obj.id
    
    def get(self, summary_id: str) -> Optional[dict]:
        """Retrieve summary by ID; return dict or None"""
        orm_obj = self.session.query(SummaryORM).filter(
            SummaryORM.id == summary_id
        ).first()
        if orm_obj:
            return self._to_dict(orm_obj)
        return None
    
    def _to_dict(self, orm_obj) -> dict:
        """Convert ORM object to dict for API response"""
        return {
            "id": orm_obj.id,
            "transcript_excerpt": orm_obj.transcript_excerpt,
            "transcript_length_words": orm_obj.transcript_length_words,
            "key_points": orm_obj.key_points,
            "decisions": orm_obj.decisions,
            "action_items": orm_obj.action_items,
            "created_at": orm_obj.created_at.isoformat() + "Z",
            "source": orm_obj.source
        }
```

**Database Schema** (SQLite):
```sql
CREATE TABLE summaries (
    id TEXT PRIMARY KEY,
    transcript_excerpt TEXT NOT NULL,
    transcript_length_words INTEGER NOT NULL,
    key_points JSON NOT NULL DEFAULT '[]',
    decisions JSON NOT NULL DEFAULT '[]',
    action_items JSON NOT NULL DEFAULT '[]',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL DEFAULT 'api'
);
```

### Example: Persistence Flow

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript_excerpt": "In this meeting, we discussed Q4 targets and reviewed the new feature launch...",
  "transcript_length_words": 245,
  "key_points": [
    "Q4 targets are on track for delivery",
    "New feature launch delayed by 2 weeks due to testing"
  ],
  "decisions": [
    "Approved budget increase for marketing team",
    "Moved launch date from Feb 28 to Mar 15"
  ],
  "action_items": [
    {
      "description": "Finalize Q4 marketing strategy and budget breakdown",
      "owner": "Sarah Chen",
      "priority": "high"
    },
    {
      "description": "Update project timeline in Jira and notify stakeholders",
      "owner": "unassigned"
    },
    {
      "description": "Coordinate with QA for extended testing phase",
      "owner": "James Wu",
      "priority": "high"
    }
  ],
  "created_at": "2026-09-11T14:32:00Z",
  "source": "api"
}
```

### Notes

- Storage implementation must support JSON serialization/deserialization of nested arrays
- No transaction requirements for MVP (single summary per request)
- No indexing requirements documented; implementation can optimize as needed
- Compliance: All fields support Constitution Principle IV (storage independence) by using abstract interface only
