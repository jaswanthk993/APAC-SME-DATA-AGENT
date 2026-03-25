"""Translation Agent — detects language and translates to English using Gemini."""

import json
import logging
from google import genai

from backend.config import settings
from backend.models import TranslationOutput

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

TRANSLATION_PROMPT = """You are a translation agent. Analyze the user's query and:
1. Detect the language of the input text.
2. If it's NOT English, translate it to English.
3. If it IS English, keep it as-is.

IMPORTANT: Return ONLY valid JSON, nothing else. No markdown, no code blocks.

Output format:
{{
    "original_query": "<the original text exactly as given>",
    "english_query": "<English translation or original if already English>",
    "language": "<detected language code, e.g., en, hi, ja, zh, ko, vi, th>"
}}

User's query: {query}"""


async def run_translation_agent(query: str) -> TranslationOutput:
    """
    Detect language and translate query to English.

    Args:
        query: The user's raw input in any language.

    Returns:
        TranslationOutput with original_query, english_query, and language.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=TRANSLATION_PROMPT.format(query=query),
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
            ),
        )

        raw_text = response.text.strip()

        # Clean potential markdown code blocks
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)

        return TranslationOutput(
            original_query=result.get("original_query", query),
            english_query=result.get("english_query", query),
            language=result.get("language", "en"),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Translation agent JSON parse error: {e}")
        # Fallback: assume English
        return TranslationOutput(
            original_query=query,
            english_query=query,
            language="en",
        )
    except Exception as e:
        logger.error(f"Translation agent error: {e}")
        return TranslationOutput(
            original_query=query,
            english_query=query,
            language="en",
        )
