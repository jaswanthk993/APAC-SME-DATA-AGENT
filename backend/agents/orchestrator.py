"""Orchestrator — runs all three agents sequentially, yielding NDJSON stream chunks."""

import json
import logging
import asyncio
from typing import AsyncGenerator

from backend.models import StreamChunk
from backend.agents.translation_agent import run_translation_agent
from backend.agents.sql_agent import run_sql_agent
from backend.agents.response_agent import run_response_agent

logger = logging.getLogger(__name__)


def _chunk(chunk_type: str, content=None, agent: str = None) -> str:
    """Create a single NDJSON line."""
    data = {"type": chunk_type}
    if content is not None:
        data["content"] = content
    if agent:
        data["agent"] = agent
    return json.dumps(data, default=str) + "\n"


async def run_pipeline(message: str) -> AsyncGenerator[str, None]:
    """
    Execute the full agent pipeline and yield NDJSON chunks.

    Pipeline: Translation → SQL → Response

    Args:
        message: The user's raw query in any language.

    Yields:
        NDJSON string chunks for each stage.
    """
    try:
        # ── Stage 1: Translation Agent ──────────────────────────
        yield _chunk("thinking", "Analyzing your query...", "translation")
        yield _chunk("agent_update", "Detecting language and translating...", "translation")

        translation = await run_translation_agent(message)

        yield _chunk(
            "agent_update",
            {
                "status": "complete",
                "language": translation.language,
                "english_query": translation.english_query,
            },
            "translation",
        )

        # ── Stage 2: SQL Agent ──────────────────────────────────
        yield _chunk("thinking", "Generating database query...", "sql")
        yield _chunk("agent_update", "Querying AlloyDB...", "sql")

        sql_output = await run_sql_agent(translation.english_query)

        if sql_output.error:
            yield _chunk(
                "agent_update",
                {"status": "error", "error": sql_output.error},
                "sql",
            )
            # Still try to generate a response with the error info
            yield _chunk("answer", f"Unable to fetch data: {sql_output.error}")
            yield _chunk("done", {"success": False, "error": sql_output.error})
            return

        yield _chunk(
            "agent_update",
            {
                "status": "complete",
                "sql": sql_output.sql,
                "row_count": sql_output.data.row_count,
            },
            "sql",
        )

        # Send raw data
        yield _chunk("data", {
            "columns": sql_output.data.columns,
            "rows": sql_output.data.rows,
            "row_count": sql_output.data.row_count,
        })

        # ── Stage 3: Response Agent ─────────────────────────────
        yield _chunk("thinking", "Generating insights...", "response")
        yield _chunk("agent_update", "Summarizing results...", "response")

        response = await run_response_agent(sql_output, translation.language)

        yield _chunk(
            "agent_update",
            {"status": "complete"},
            "response",
        )

        # Send final response components
        yield _chunk("answer", response.answer)
        yield _chunk("insight", response.insight)
        yield _chunk("chart", {
            "type": response.chart_type,
            "columns": response.data.columns,
            "rows": response.data.rows,
        })

        yield _chunk("done", {
            "success": True,
            "language": response.language,
            "source": response.source,
        })

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        yield _chunk("agent_update", {"status": "error", "error": str(e)}, "system")
        yield _chunk("answer", f"An error occurred: {str(e)}")
        yield _chunk("done", {"success": False, "error": str(e)})
