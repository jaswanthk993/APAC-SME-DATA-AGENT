"""SQL Agent — generates SQL from natural language, validates, and executes on AlloyDB."""

import json
import logging
from google import genai

from backend.config import settings
from backend.database import execute_query, get_schema_info
from backend.security import validate_sql
from backend.models import SQLOutput, SQLData

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

SQL_GENERATION_PROMPT = """You are a SQL expert agent. Given a database schema and a natural language question, generate a PostgreSQL SELECT query to answer it.

DATABASE SCHEMA:
{schema}

RULES:
1. ONLY generate SELECT queries — no INSERT, UPDATE, DELETE, or DROP
2. Always include LIMIT 20 unless the query specifically asks for all results
3. NEVER use SELECT * — always specify column names
4. Use JOINs when data from multiple tables is needed
5. Use meaningful column aliases for readability
6. For aggregations, always include GROUP BY
7. Order results logically (e.g., by amount DESC, by date DESC)

Also suggest a chart type for visualizing the results:
- "bar" — for comparing categories
- "line" — for time-series/trends
- "pie" — for proportions/distributions
- "none" — for detailed listings or single values

IMPORTANT: Return ONLY valid JSON, no markdown, no code blocks.

Output format:
{{
    "sql": "<the SQL query>",
    "chart_type": "bar|line|pie|none"
}}

Question: {question}"""


async def run_sql_agent(english_query: str) -> SQLOutput:
    """
    Generate SQL from natural language, validate it, and execute on AlloyDB.

    Args:
        english_query: The user's question translated to English.

    Returns:
        SQLOutput with sql, data, chart_type, and any error.
    """
    try:
        # Step 1: Get database schema for context
        schema = await get_schema_info()

        # Step 2: Generate SQL using Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=SQL_GENERATION_PROMPT.format(
                schema=schema, question=english_query
            ),
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000,
            ),
        )

        raw_text = response.text.strip()

        # Clean potential markdown
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)
        sql = result.get("sql", "")
        chart_type = result.get("chart_type", "none")

        # Step 3: Validate SQL for security
        is_safe, error_msg = validate_sql(sql)
        if not is_safe:
            logger.warning(f"🚫 Unsafe SQL blocked: {error_msg}")
            return SQLOutput(
                sql=sql,
                chart_type="none",
                error=f"Security: {error_msg}",
            )

        # Step 4: Execute on AlloyDB
        data = await execute_query(sql)

        return SQLOutput(
            sql=sql,
            data=SQLData(**data),
            chart_type=chart_type,
        )

    except json.JSONDecodeError as e:
        logger.error(f"SQL agent JSON parse error: {e}")
        return SQLOutput(error=f"Failed to parse SQL generation response: {str(e)}")

    except Exception as e:
        logger.error(f"SQL agent error: {e}")
        return SQLOutput(error=f"Query execution failed: {str(e)}")
