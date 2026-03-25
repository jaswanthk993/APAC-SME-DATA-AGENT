"""Response Agent — summarizes SQL results and translates back to user's language."""

import json
import logging
from google import genai

from backend.config import settings
from backend.models import SQLOutput, ResponseOutput

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

RESPONSE_PROMPT = """You are a data insights agent. Given SQL query results, generate a clear, concise response.

SQL Query: {sql}
Result Columns: {columns}
Result Data (first rows): {rows}
Total Rows: {row_count}
User's Original Language: {language}

INSTRUCTIONS:
1. Write a SHORT answer (under 50 words) summarizing the key finding
2. Provide ONE actionable business insight based on the data
3. BOTH the answer AND insight MUST be in the user's language: {language_name}
   - If the language is "en" (English), write in English
   - If the language is "hi" (Hindi), write in Hindi
   - If the language is "ja" (Japanese), write in Japanese
   - And so on for any other language
4. Keep it professional but easy to understand for SME business owners

IMPORTANT: Return ONLY valid JSON, no markdown, no code blocks.

Output format:
{{
    "answer": "<short answer in user's language, under 50 words>",
    "insight": "<one actionable insight in user's language>"
}}"""

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "vi": "Vietnamese",
    "th": "Thai",
    "ms": "Malay",
    "id": "Indonesian",
    "tl": "Filipino/Tagalog",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ar": "Arabic",
}


async def run_response_agent(
    sql_output: SQLOutput, language: str
) -> ResponseOutput:
    """
    Generate a human-readable summary of SQL results in the user's language.

    Args:
        sql_output: The SQL agent's output with query and data.
        language: The user's detected language code.

    Returns:
        ResponseOutput with answer, insight, chart_type, language, source, data.
    """
    try:
        language_name = LANGUAGE_NAMES.get(language, "English")

        # Prepare data preview (first 10 rows for context)
        rows_preview = sql_output.data.rows[:10] if sql_output.data.rows else []

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=RESPONSE_PROMPT.format(
                sql=sql_output.sql,
                columns=sql_output.data.columns,
                rows=json.dumps(rows_preview, default=str),
                row_count=sql_output.data.row_count,
                language=language,
                language_name=language_name,
            ),
            config=genai.types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=800,
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

        return ResponseOutput(
            answer=result.get("answer", "Unable to generate response."),
            insight=result.get("insight", ""),
            chart_type=sql_output.chart_type,
            language=language,
            source="alloydb",
            data=sql_output.data,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Response agent JSON parse error: {e}")
        return ResponseOutput(
            answer="Unable to parse the response. Please try rephrasing your question.",
            insight="",
            chart_type=sql_output.chart_type,
            language=language,
            source="alloydb",
            data=sql_output.data,
        )

    except Exception as e:
        logger.error(f"Response agent error: {e}")
        return ResponseOutput(
            answer=f"Error generating response: {str(e)}",
            insight="",
            chart_type="none",
            language=language,
            source="alloydb",
        )
