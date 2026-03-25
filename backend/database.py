"""AlloyDB (PostgreSQL) database connection and query execution."""

import asyncpg
import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# Connection pool (initialized on startup)
_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize the async connection pool to AlloyDB."""
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("✅ Connected to AlloyDB")
    except Exception as e:
        logger.error(f"❌ Failed to connect to AlloyDB: {e}")
        raise


async def close_db():
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Database connection pool closed")


async def check_health() -> bool:
    """Check database connectivity."""
    try:
        if not _pool:
            return False
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False


async def execute_query(sql: str) -> dict:
    """
    Execute a read-only SQL query and return structured results.

    Returns:
        {
            "columns": [...],
            "rows": [[...], ...],
            "row_count": int
        }
    """
    if not _pool:
        raise ConnectionError("Database not connected")

    async with _pool.acquire() as conn:
        # Use a read-only transaction for safety
        async with conn.transaction(readonly=True):
            stmt = await conn.prepare(sql)
            records = await stmt.fetch()

            if not records:
                return {"columns": [], "rows": [], "row_count": 0}

            columns = [attr.name for attr in stmt.get_attributes()]
            rows = []
            for record in records:
                row = []
                for col in columns:
                    val = record[col]
                    # Convert non-serializable types to string
                    if isinstance(val, (bytes, bytearray)):
                        val = val.hex()
                    elif hasattr(val, "isoformat"):
                        val = val.isoformat()
                    elif not isinstance(val, (str, int, float, bool, type(None))):
                        val = str(val)
                    row.append(val)
                rows.append(row)

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }


async def get_schema_info() -> str:
    """
    Retrieve the database schema for agent context.
    Returns a formatted string describing all tables and columns.
    """
    if not _pool:
        raise ConnectionError("Database not connected")

    schema_sql = """
    SELECT 
        t.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable
    FROM information_schema.tables t
    JOIN information_schema.columns c 
        ON t.table_name = c.table_name AND t.table_schema = c.table_schema
    WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position
    """

    async with _pool.acquire() as conn:
        records = await conn.fetch(schema_sql)

    if not records:
        return "No tables found in the database."

    # Group by table
    tables = {}
    for r in records:
        table = r["table_name"]
        if table not in tables:
            tables[table] = []
        nullable = "NULL" if r["is_nullable"] == "YES" else "NOT NULL"
        tables[table].append(f"  - {r['column_name']} ({r['data_type']}, {nullable})")

    lines = []
    for table, cols in tables.items():
        lines.append(f"TABLE: {table}")
        lines.extend(cols)
        lines.append("")

    return "\n".join(lines)
