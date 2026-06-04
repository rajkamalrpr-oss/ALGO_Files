"""
app/db/settings_store.py — Persist bot settings in MongoDB.
"""

from app.db.database import get_db

_COLLECTION = "bot_settings"
_ID = "main"

_DEFAULTS: dict = {
    "_id": _ID,
    "binance_api_key": "",
    "binance_api_secret": "",
    "binance_testnet": True,
    "binance_base_url": "https://testnet.binancefuture.com",
}

_ALLOWED_KEYS = {"binance_api_key", "binance_api_secret", "binance_testnet", "binance_base_url"}


async def get_settings() -> dict:
    db = get_db()
    doc = await db[_COLLECTION].find_one({"_id": _ID})
    return doc if doc else dict(_DEFAULTS)


async def save_settings(updates: dict) -> dict:
    db = get_db()
    patch = {k: v for k, v in updates.items() if k in _ALLOWED_KEYS}
    if patch:
        await db[_COLLECTION].update_one({"_id": _ID}, {"$set": patch}, upsert=True)
    return await get_settings()
