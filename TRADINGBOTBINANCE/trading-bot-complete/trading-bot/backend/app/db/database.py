"""
app/db/database.py — Async MongoDB client via Motor.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("db")

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_url)
    # Verify connection
    await _client.admin.command("ping")
    logger.info(f"Connected to MongoDB at {settings.mongodb_url}")


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Database not initialised. Call connect_db() first.")
    return _client[settings.mongodb_db]
