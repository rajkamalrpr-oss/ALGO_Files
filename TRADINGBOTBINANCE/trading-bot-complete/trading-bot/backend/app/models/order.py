"""
app/models/order.py — Pydantic models for orders (request, response, DB document).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"


class OrderStatus(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# ── Request model (CLI / API input) ───────────────────────────────────────────

class PlaceOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, examples=["BTCUSDT"])
    side: OrderSide
    order_type: OrderType = Field(..., alias="type")
    quantity: Decimal = Field(..., gt=0, examples=[0.001])
    price: Optional[Decimal] = Field(None, gt=0, examples=[67000.0])
    stop_price: Optional[Decimal] = Field(None, gt=0, examples=[65000.0])
    time_in_force: str = Field("GTC", pattern="^(GTC|IOC|FOK)$")

    model_config = {"populate_by_name": True}

    @field_validator("symbol", mode="before")
    @classmethod
    def upper_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v, info):
        return v

    def model_post_init(self, __context) -> None:
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("price is required for LIMIT orders")
        if self.order_type == OrderType.STOP_MARKET and self.stop_price is None:
            raise ValueError("stop_price is required for STOP_MARKET orders")
        if self.order_type == OrderType.MARKET and self.price is not None:
            raise ValueError("price must not be provided for MARKET orders")


# ── DB / response model ───────────────────────────────────────────────────────

class OrderDocument(BaseModel):
    """Stored in MongoDB after a successful order placement."""

    id: Optional[str] = Field(None, alias="_id")
    order_id: int
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    price: float
    orig_qty: float
    executed_qty: float
    avg_price: float
    time_in_force: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_response: dict

    model_config = {"populate_by_name": True}


class OrderResponse(BaseModel):
    """API response returned to the frontend."""

    id: Optional[str] = None
    order_id: int
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    price: float
    orig_qty: float
    executed_qty: float
    avg_price: float
    time_in_force: str
    created_at: datetime
    fill_percent: float = 0.0

    @classmethod
    def from_document(cls, doc: dict) -> "OrderResponse":
        orig = float(doc.get("orig_qty", 0))
        executed = float(doc.get("executed_qty", 0))
        fill_pct = (executed / orig * 100) if orig > 0 else 0.0
        return cls(
            id=str(doc.get("_id", "")),
            order_id=doc["order_id"],
            client_order_id=doc["client_order_id"],
            symbol=doc["symbol"],
            side=doc["side"],
            order_type=doc["order_type"],
            status=doc["status"],
            price=float(doc.get("price", 0)),
            orig_qty=orig,
            executed_qty=executed,
            avg_price=float(doc.get("avg_price", 0)),
            time_in_force=doc.get("time_in_force", ""),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            fill_percent=round(fill_pct, 2),
        )
