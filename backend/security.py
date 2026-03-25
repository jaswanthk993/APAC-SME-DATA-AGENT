"""SQL security validation — block dangerous operations."""

import re
import logging

logger = logging.getLogger(__name__)

# Blocked SQL keywords (case-insensitive)
BLOCKED_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"--",
    r";.*;",  # Multiple statements
]


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL query for safety.

    Returns:
        (is_safe, error_message)
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query"

    sql_upper = sql.strip().upper()

    # Must start with SELECT or WITH (for CTEs)
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        return False, "Only SELECT queries are allowed"

    # Check for blocked keywords
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, sql_upper):
            keyword = pattern.replace(r"\b", "").strip()
            logger.warning(f"🚫 Blocked SQL keyword detected: {keyword}")
            return False, f"Blocked operation: {keyword} is not allowed"

    # Check for multiple statements (semicolons not at end)
    clean_sql = sql.strip().rstrip(";")
    if ";" in clean_sql:
        return False, "Multiple SQL statements are not allowed"

    return True, ""
