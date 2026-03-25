"""FastAPI application — health endpoint, chat streaming, and static file serving."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import init_db, close_db, check_health
from backend.models import ChatRequest, HealthResponse
from backend.agents.orchestrator import run_pipeline

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# App
app = FastAPI(
    title="SME Data Copilot",
    description="AI-powered multilingual data assistant for SMEs using Gemini + AlloyDB",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database connection on startup."""
    logger.info("🚀 Starting SME Data Copilot...")
    try:
        await init_db()
        logger.info("✅ Database connected")
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {e}")
        logger.warning("Server will start without database. Queries will fail until DB is available.")


@app.on_event("shutdown")
async def shutdown():
    """Clean up database connections."""
    await close_db()
    logger.info("👋 Shutting down")


# ── Health Endpoint ─────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — returns agent status and database connectivity."""
    db_status = "connected" if await check_health() else "disconnected"
    return HealthResponse(
        status="ok",
        agents=["translation", "sql", "response"],
        database=db_status,
    )


# ── Seed Endpoint ──────────────────────────────────────────
@app.post("/api/seed")
async def seed_database():
    """Run the seed.sql script to populate the database with demo data."""
    try:
        from backend.config import settings
        import asyncpg
        
        # Connect explicitly to run multi-statement SQL
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        
        seed_path = Path(__file__).parent / "seed.sql"
        if not seed_path.exists():
            return JSONResponse(status_code=404, content={"error": "seed.sql not found"})
            
        sql = seed_path.read_text(encoding="utf-8")
        await conn.execute(sql)
        await conn.close()
        
        return {"status": "success", "message": "Database seeded successfully!"}
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Advanced Query Endpoint ───────────────────────────────────────
@app.get("/api/advanced")
async def advanced_dashboard():
    """Execute the Advanced Query #10 on AlloyDB and return raw data."""
    from backend.database import execute_query
    import json
    import decimal
    import datetime

    sql = """
    WITH rev AS (
      SELECT
        b.id,
        b.industry AS category,
        b.name AS business_name,
        b.city,
        SUM(t.total_amount)           AS revenue,
        COUNT(t.id)                   AS txn_count,
        COUNT(DISTINCT t.product_id)  AS unique_products,
        MAX(t.transaction_date)       AS last_sale_date
      FROM transactions t
      JOIN businesses b ON b.id = t.business_id
      GROUP BY b.id, b.industry, b.name, b.city
    ),
    cat_summary AS (
      SELECT
        category,
        COUNT(*)                      AS businesses,
        SUM(revenue)                  AS cat_revenue,
        SUM(txn_count)                AS cat_txns,
        MAX(revenue)                  AS top_biz_revenue,
        ROUND(AVG(revenue), 0)        AS avg_biz_revenue
      FROM rev
      GROUP BY category
    ),
    grand AS (
      SELECT SUM(cat_revenue) AS total
      FROM cat_summary
    )
    SELECT
      cs.category,
      cs.businesses,
      cs.cat_txns                     AS transactions,
      cs.cat_revenue                  AS total_revenue,
      cs.avg_biz_revenue              AS avg_per_business,
      ROUND(
        cs.cat_revenue * 100.0 / g.total, 1
      )                               AS revenue_share_pct,
      (
        SELECT r2.business_name
        FROM rev r2
        WHERE r2.category = cs.category
        ORDER BY r2.revenue DESC
        LIMIT 1
      )                               AS top_business,
      (
        SELECT r2.city
        FROM rev r2
        WHERE r2.category = cs.category
        ORDER BY r2.revenue DESC
        LIMIT 1
      )                               AS top_city
    FROM cat_summary cs
    CROSS JOIN grand g
    ORDER BY cs.cat_revenue DESC;
    """
    
    try:
        result = await execute_query(sql)
        
        def default_serializer(obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            return str(obj)

        return JSONResponse(content=json.loads(json.dumps(result, default=default_serializer)))
    except Exception as e:
        logger.error(f"Advanced query error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Chat Endpoint (NDJSON Streaming) ───────────────────────
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Process a user message through the agent pipeline.
    Returns an NDJSON stream with real-time updates.
    """
    logger.info(f"📩 New query: {request.message[:100]}")

    async def generate():
        async for chunk in run_pipeline(request.message):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Serve Frontend Static Files ────────────────────────────
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


# ── Run with Uvicorn ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=True,
    )
