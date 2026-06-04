"""
app/main.py — FastAPI application entry point.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import orders, account
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.database import connect_db, close_db
from app.services.binance import close_binance_client, get_binance_client
from app.services.order_service import sync_new_orders

setup_logging(settings.log_level)
logger = get_logger("main")

ORDER_SYNC_INTERVAL = 1  # seconds


async def _order_sync_loop() -> None:
    """Background task: keep NEW/PARTIALLY_FILLED orders in sync with Binance."""
    while True:
        await asyncio.sleep(ORDER_SYNC_INTERVAL)
        try:
            client = get_binance_client()
            db_module = __import__("app.db.database", fromlist=["get_db"])
            db = db_module.get_db()
            result = await sync_new_orders(client, db)
            if result["updated"] > 0:
                logger.info(f"Auto-sync: updated {result['updated']} order(s)")
        except Exception as e:
            logger.warning(f"Auto-sync error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Trading Bot API...")
    await connect_db()
    sync_task = asyncio.create_task(_order_sync_loop())
    yield
    # Shutdown
    logger.info("Shutting down Trading Bot API...")
    sync_task.cancel()
    await close_db()
    await close_binance_client()


app = FastAPI(
    title="Binance Futures Trading Bot API",
    description="REST API for placing and tracking orders on Binance USDT-M Futures Testnet.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — allow React dev server ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(orders.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Binance Futures Trading Bot", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
