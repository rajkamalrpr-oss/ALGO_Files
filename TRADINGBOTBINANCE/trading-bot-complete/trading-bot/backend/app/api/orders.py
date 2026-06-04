"""
app/api/orders.py — FastAPI router for order endpoints.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.database import get_db
from app.models.order import PlaceOrderRequest, OrderResponse
from app.services.binance import get_binance_client, BinanceAPIError, BinanceAuthError, BinanceNetworkError
from app.services.order_service import place_and_store_order, get_order_history, get_order_count, get_pnl_stats, sync_new_orders
from app.core.logging import get_logger

logger = get_logger("api.orders")

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
async def place_order(request: PlaceOrderRequest):
    """Place a new MARKET, LIMIT, or STOP_MARKET order on Binance Futures Testnet."""
    client = get_binance_client()
    db = get_db()
    try:
        result = await place_and_store_order(request, client, db)
        logger.info(f"Order API success: orderId={result.order_id} status={result.status}")
        return result
    except BinanceAuthError as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e.message}")
    except BinanceAPIError as e:
        logger.error(f"Binance API error: {e}")
        raise HTTPException(status_code=400, detail=f"Binance error [{e.code}]: {e.message}")
    except BinanceNetworkError as e:
        logger.error(f"Network error: {e}")
        raise HTTPException(status_code=503, detail=f"Network error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error placing order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=dict)
async def list_orders(
    symbol: Optional[str] = Query(None, description="Filter by symbol, e.g. BTCUSDT"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """Retrieve order history from MongoDB."""
    db = get_db()
    orders = await get_order_history(db, symbol=symbol, limit=limit, skip=skip)
    total = await get_order_count(db, symbol=symbol)
    return {"orders": [o.model_dump() for o in orders], "total": total, "limit": limit, "skip": skip}


@router.get("/stats/pnl")
async def pnl_stats(today: bool = Query(False, description="Restrict to today's orders (UTC)")):
    """Aggregate P&L statistics from order history."""
    db = get_db()
    since = None
    if today:
        now = datetime.now(timezone.utc)
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    stats = await get_pnl_stats(db, since=since)
    return stats


@router.post("/sync")
async def sync_orders():
    """Re-fetch fill data for all NEW orders from Binance and update MongoDB."""
    client = get_binance_client()
    db = get_db()
    try:
        result = await sync_new_orders(client, db)
        return result
    except BinanceAuthError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e.message}")
    except BinanceNetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))
