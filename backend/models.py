"""Pydantic models for all request/response schemas."""

from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    message: str


class TranslationOutput(BaseModel):
    """Output from the Translation Agent."""
    original_query: str
    english_query: str
    language: str


class SQLData(BaseModel):
    """Structured query result data."""
    columns: list[str] = []
    rows: list[list[Any]] = []
    row_count: int = 0


class SQLOutput(BaseModel):
    """Output from the SQL Agent."""
    sql: str = ""
    data: SQLData = SQLData()
    chart_type: str = "none"
    error: Optional[str] = None


class ResponseOutput(BaseModel):
    """Output from the Response Agent."""
    answer: str
    insight: str
    chart_type: str = "none"
    language: str = "en"
    source: str = "alloydb"
    data: SQLData = SQLData()


class StreamChunk(BaseModel):
    """A single chunk in the NDJSON stream."""
    type: str  # thinking, agent_update, answer, data, insight, chart, done
    content: Any = None
    agent: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agents: list[str]
    database: str
