"""
app/services/order_service.py — Order business logic: place, store, retrieve.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.models.order import OrderDocument, OrderResponse, PlaceOrderRequest
from app.services.binance import BinanceFuturesClient

logger = get_logger("order_service")

COLLECTION = "orders"


async def place_and_store_order(
    request: PlaceOrderRequest,
    client: BinanceFuturesClient,
    db: AsyncIOMotorDatabase,
) -> OrderResponse:
    """Place an order on Binance, persist to MongoDB, return normalised response."""

    # ── Build Binance params ──────────────────────────────────────────────────
    params: dict = {
        "symbol": request.symbol,
        "side": request.side.value,
        "type": request.order_type.value,
        "quantity": str(request.quantity),
    }
    if request.price is not None:
        params["price"] = str(request.price)
        params["timeInForce"] = request.time_in_force
    if request.stop_price is not None:
        params["stopPrice"] = str(request.stop_price)

    # ── Place on Binance ──────────────────────────────────────────────────────
    raw = await client.place_order(**params)

    # For MARKET orders, the testnet placement response often shows status=NEW
    # with executedQty=0. Re-fetch once after a short delay to capture fill data.
    if params.get("type") == "MARKET" and raw.get("status") != "FILLED":
        order_id = raw.get("orderId")
        symbol_str = raw.get("symbol", request.symbol)
        if order_id:
            for attempt in range(3):
                await asyncio.sleep(0.4 * (attempt + 1))
                try:
                    updated = await client.get_order(symbol_str, order_id)
                    raw = updated
                    if updated.get("status") in ("FILLED", "PARTIALLY_FILLED"):
                        break
                except Exception:
                    break

    # ── Persist to MongoDB ────────────────────────────────────────────────────
    doc = {
        "order_id": raw.get("orderId", 0),
        "client_order_id": raw.get("clientOrderId", ""),
        "symbol": raw.get("symbol", request.symbol),
        "side": raw.get("side", request.side.value),
        "order_type": raw.get("type", request.order_type.value),
        "status": raw.get("status", "UNKNOWN"),
        "price": float(raw.get("price", 0)),
        "orig_qty": float(raw.get("origQty", str(request.quantity))),
        "executed_qty": float(raw.get("executedQty", 0)),
        "avg_price": float(raw.get("avgPrice", 0)),
        "time_in_force": raw.get("timeInForce", request.time_in_force),
        "created_at": datetime.now(timezone.utc),
        "raw_response": raw,
    }

    result = await db[COLLECTION].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    logger.info(f"Order persisted to MongoDB: _id={doc['_id']} orderId={doc['order_id']}")

    return OrderResponse.from_document(doc)


async def get_order_history(
    db: AsyncIOMotorDatabase,
    symbol: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[OrderResponse]:
    """Retrieve order history from MongoDB."""
    query = {}
    if symbol:
        query["symbol"] = symbol.upper()

    cursor = db[COLLECTION].find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [OrderResponse.from_document(d) for d in docs]


async def get_order_count(db: AsyncIOMotorDatabase, symbol: Optional[str] = None) -> int:
    query = {}
    if symbol:
        query["symbol"] = symbol.upper()
    return await db[COLLECTION].count_documents(query)


async def get_pnl_stats(db: AsyncIOMotorDatabase, since: Optional[datetime] = None) -> dict:
    """Compute basic P&L stats from stored orders."""
    # "effective_qty" uses executed_qty when available, falls back to orig_qty
    # for MARKET orders where testnet returns executedQty=0.
    _effective_qty = {
        "$cond": [
            {"$and": [{"$eq": ["$order_type", "MARKET"]}, {"$eq": ["$executed_qty", 0]}]},
            "$orig_qty",
            "$executed_qty",
        ]
    }
    # "is_filled" — FILLED/PARTIALLY_FILLED statuses, plus MARKET orders that
    # aren't canceled/rejected/expired (testnet often leaves them as NEW).
    _is_filled = {
        "$cond": [
            {
                "$or": [
                    {"$in": ["$status", ["FILLED", "PARTIALLY_FILLED"]]},
                    {
                        "$and": [
                            {"$eq": ["$order_type", "MARKET"]},
                            {"$not": {"$in": ["$status", ["CANCELED", "REJECTED", "EXPIRED"]]}},
                        ]
                    },
                ]
            },
            1, 0,
        ]
    }

    pipeline = []
    if since:
        pipeline.append({"$match": {"created_at": {"$gte": since}}})
    pipeline += [
        {
            "$group": {
                "_id": "$symbol",
                "total_orders": {"$sum": 1},
                "total_buy_qty": {
                    "$sum": {"$cond": [{"$eq": ["$side", "BUY"]}, _effective_qty, 0]}
                },
                "total_sell_qty": {
                    "$sum": {"$cond": [{"$eq": ["$side", "SELL"]}, _effective_qty, 0]}
                },
                "total_buy_value": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$side", "BUY"]},
                            {"$multiply": [_effective_qty, {"$cond": [{"$gt": ["$avg_price", 0]}, "$avg_price", "$price"]}]},
                            0,
                        ]
                    }
                },
                "total_sell_value": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$side", "SELL"]},
                            {"$multiply": [_effective_qty, {"$cond": [{"$gt": ["$avg_price", 0]}, "$avg_price", "$price"]}]},
                            0,
                        ]
                    }
                },
                "filled_orders": {"$sum": _is_filled},
            }
        },
        {"$sort": {"total_orders": -1}},
    ]

    cursor = db[COLLECTION].aggregate(pipeline)
    results = await cursor.to_list(length=100)

    total_orders = sum(r["total_orders"] for r in results)
    total_filled = sum(r["filled_orders"] for r in results)

    # Only count closed (matched) portions — open positions are unrealised, not realised.
    # matched_qty = min(buy_qty, sell_qty) per symbol.
    realized_pnl = 0.0
    for r in results:
        bq = r["total_buy_qty"]
        sq = r["total_sell_qty"]
        bv = r["total_buy_value"]
        sv = r["total_sell_value"]
        matched = min(bq, sq)
        if matched > 0 and bq > 0 and sv > 0:
            avg_buy = bv / bq
            avg_sell = sv / sq
            realized_pnl += (avg_sell - avg_buy) * matched

    has_price_data = any(
        r["total_buy_value"] > 0 or r["total_sell_value"] > 0
        for r in results
    )

    return {
        "total_orders": total_orders,
        "filled_orders": total_filled,
        "fill_rate": round(total_filled / total_orders * 100, 1) if total_orders else 0,
        "realized_pnl": round(realized_pnl, 4),
        "has_price_data": has_price_data,
        "by_symbol": results,
    }


async def sync_new_orders(
    client: "BinanceFuturesClient",
    db: AsyncIOMotorDatabase,
) -> dict:
    """Re-fetch fill data for every NEW order from Binance and update MongoDB."""
    cursor = db[COLLECTION].find({"status": {"$in": ["NEW", "PARTIALLY_FILLED"]}})
    orders = await cursor.to_list(length=1000)

    checked = len(orders)
    updated = 0
    failed = 0

    for order in orders:
        try:
            raw = await client.get_order(order["symbol"], order["order_id"])
            new_status = raw.get("status", order["status"])
            new_exec_qty = float(raw.get("executedQty", order.get("executed_qty", 0)))
            new_avg_price = float(raw.get("avgPrice", order.get("avg_price", 0)))
            new_price = float(raw.get("price", order.get("price", 0)))

            changed = (
                new_status != order.get("status")
                or new_exec_qty != order.get("executed_qty")
                or new_avg_price != order.get("avg_price")
            )
            if changed:
                await db[COLLECTION].update_one(
                    {"_id": order["_id"]},
                    {"$set": {
                        "status": new_status,
                        "executed_qty": new_exec_qty,
                        "avg_price": new_avg_price,
                        "price": new_price,
                    }},
                )
                updated += 1
        except Exception as e:
            logger.warning(f"Sync failed for order {order.get('order_id')}: {e}")
            failed += 1

    logger.info(f"Sync complete: checked={checked} updated={updated} failed={failed}")
    return {"checked": checked, "updated": updated, "failed": failed}
