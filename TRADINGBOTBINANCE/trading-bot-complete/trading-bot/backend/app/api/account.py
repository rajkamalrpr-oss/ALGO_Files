"""
app/api/account.py — FastAPI router for account/balance endpoints.
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import get_db
from app.models.order import OrderResponse
from app.services.binance import get_binance_client, close_binance_client, BinanceAPIError, BinanceNetworkError
from app.core.logging import get_logger

logger = get_logger("api.account")

router = APIRouter(prefix="/account", tags=["Account"])

_ENV_FILE = Path(".env")


class CredentialsRequest(BaseModel):
    api_key: str
    api_secret: str


def _persist_credentials(api_key: str, api_secret: str) -> None:
    lines = _ENV_FILE.read_text().splitlines() if _ENV_FILE.exists() else []
    key_done = secret_done = False
    for i, line in enumerate(lines):
        if line.startswith("BINANCE_API_KEY="):
            lines[i] = f"BINANCE_API_KEY={api_key}"
            key_done = True
        elif line.startswith("BINANCE_API_SECRET="):
            lines[i] = f"BINANCE_API_SECRET={api_secret}"
            secret_done = True
    if not key_done:
        lines.append(f"BINANCE_API_KEY={api_key}")
    if not secret_done:
        lines.append(f"BINANCE_API_SECRET={api_secret}")
    _ENV_FILE.write_text("\n".join(lines) + "\n")


@router.get("/balance")
async def get_balance():
    """Fetch wallet balances from Binance Futures Testnet."""
    client = get_binance_client()
    try:
        balances = await client.get_balance()
        return {"balances": balances}
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=f"Binance error [{e.code}]: {e.message}")
    except BinanceNetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/positions")
async def get_positions():
    """Fetch open positions from Binance Futures Testnet."""
    client = get_binance_client()
    try:
        positions = await client.get_positions()
        return {"positions": positions}
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=f"Binance error [{e.code}]: {e.message}")
    except BinanceNetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """Get 24-hour ticker stats for a symbol."""
    client = get_binance_client()
    try:
        ticker = await client.get_24hr_ticker(symbol.upper())
        return ticker
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=f"Binance error [{e.code}]: {e.message}")
    except BinanceNetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/ping")
async def ping():
    """Health check — verifies Binance API connectivity."""
    client = get_binance_client()
    ok = await client.ping()
    return {"binance_reachable": ok}


@router.get("/credentials")
async def get_credentials():
    """Return masked credential status (never returns the full secret)."""
    key = settings.binance_api_key
    if key and len(key) > 10:
        preview = f"{key[:6]}...{key[-4:]}"
    elif key:
        preview = "set"
    else:
        preview = "not set"
    return {"api_key_set": bool(key), "api_key_preview": preview}


@router.post("/positions/{symbol}/exit", response_model=OrderResponse)
async def exit_position(
    symbol: str,
    qty: float = Query(None, gt=0, description="Quantity to exit; omit to close full position"),
):
    """Square off an open position (full or partial) with a reduceOnly MARKET order."""
    symbol = symbol.upper()
    client = get_binance_client()

    try:
        positions = await client.get_positions()
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=f"Binance error [{e.code}]: {e.message}")
    except BinanceNetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))

    position = next((p for p in positions if p["symbol"] == symbol), None)
    if position is None:
        raise HTTPException(status_code=404, detail=f"No open position found for {symbol}")

    position_amt = float(position.get("positionAmt", 0))
    if position_amt == 0:
        raise HTTPException(status_code=400, detail=f"{symbol} has no open position to exit")

    exit_side = "SELL" if position_amt > 0 else "BUY"
    max_qty = abs(position_amt)

    if qty is None:
        quantity = max_qty
    elif qty > max_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Requested qty {qty} exceeds open position size {max_qty}",
        )
    else:
        quantity = qty

    try:
        raw = await client.place_order(
            symbol=symbol,
            side=exit_side,
            type="MARKET",
            quantity=str(quantity),
            reduceOnly="true",
        )
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=f"Binance error [{e.code}]: {e.message}")
    except BinanceNetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))

    db = get_db()
    doc = {
        "order_id": raw.get("orderId", 0),
        "client_order_id": raw.get("clientOrderId", ""),
        "symbol": raw.get("symbol", symbol),
        "side": raw.get("side", exit_side),
        "order_type": raw.get("type", "MARKET"),
        "status": raw.get("status", "UNKNOWN"),
        "price": float(raw.get("price", 0)),
        "orig_qty": float(raw.get("origQty", str(quantity))),
        "executed_qty": float(raw.get("executedQty", 0)),
        "avg_price": float(raw.get("avgPrice", 0)),
        "time_in_force": raw.get("timeInForce", "GTC"),
        "created_at": datetime.now(timezone.utc),
        "raw_response": raw,
    }
    result = await db["orders"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    logger.info(f"Exit order stored: symbol={symbol} side={exit_side} qty={quantity}")
    return OrderResponse.from_document(doc)


@router.post("/credentials")
async def set_credentials(body: CredentialsRequest):
    """Update Binance API credentials at runtime and persist to .env."""
    if not body.api_key.strip() or not body.api_secret.strip():
        raise HTTPException(status_code=422, detail="api_key and api_secret must not be empty")

    settings.binance_api_key = body.api_key.strip()
    settings.binance_api_secret = body.api_secret.strip()

    await close_binance_client()
    _persist_credentials(body.api_key.strip(), body.api_secret.strip())

    key = body.api_key.strip()
    preview = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "set"
    logger.info(f"Credentials updated, key preview={preview}")
    return {"ok": True, "api_key_set": True, "api_key_preview": preview}
