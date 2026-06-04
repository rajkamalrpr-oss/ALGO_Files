"""
app/services/binance.py — Async Binance Futures REST client with HMAC signing.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("binance")


# ── Exceptions ────────────────────────────────────────────────────────────────

class BinanceAPIError(Exception):
    def __init__(self, code: int, message: str, http_status: int = 0):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(f"Binance [{code}]: {message}")


class BinanceAuthError(BinanceAPIError):
    pass


class BinanceNetworkError(Exception):
    pass


# ── Client ────────────────────────────────────────────────────────────────────

class BinanceFuturesClient:
    def __init__(self) -> None:
        self._api_key = settings.binance_api_key
        self._secret = settings.binance_api_secret.encode()
        self._base_url = settings.binance_base_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"X-MBX-APIKEY": self._api_key},
            timeout=10.0,
        )
        logger.info(f"BinanceFuturesClient ready → {self._base_url}")

    async def close(self) -> None:
        await self._client.aclose()

    # ── Signing ───────────────────────────────────────────────────────────────

    @staticmethod
    def _ts() -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        qs = urlencode(params)
        return hmac.new(self._secret, qs.encode(), hashlib.sha256).hexdigest()

    # ── HTTP ──────────────────────────────────────────────────────────────────

    async def _request(
        self, method: str, path: str, params: dict | None = None, signed: bool = False
    ) -> Any:
        params = params or {}
        if signed:
            params["timestamp"] = self._ts()
            params["recvWindow"] = 5000
            params["signature"] = self._sign(params)

        logger.debug(f"→ {method} {path} params={list(params.keys())}")
        try:
            if method == "GET":
                resp = await self._client.get(path, params=params)
            elif method == "POST":
                resp = await self._client.post(path, data=params)
            elif method == "DELETE":
                resp = await self._client.delete(path, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
        except httpx.TimeoutException as e:
            raise BinanceNetworkError("Request timed out") from e
        except httpx.ConnectError as e:
            raise BinanceNetworkError(f"Connection failed: {e}") from e
        except httpx.RequestError as e:
            raise BinanceNetworkError(str(e)) from e

        logger.debug(f"← HTTP {resp.status_code}")
        try:
            body = resp.json()
        except Exception:
            raise BinanceAPIError(0, f"Non-JSON response: {resp.text[:200]}", resp.status_code)

        if isinstance(body, dict) and "code" in body and body["code"] != 200:
            code = body["code"]
            msg = body.get("msg", "Unknown error")
            logger.error(f"Binance error code={code} msg={msg}")
            if code in (-2014, -1022):
                raise BinanceAuthError(code, msg, resp.status_code)
            raise BinanceAPIError(code, msg, resp.status_code)

        if not resp.is_success:
            raise BinanceAPIError(resp.status_code, str(body), resp.status_code)

        return body

    # ── Public API ────────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        try:
            await self._request("GET", "/fapi/v1/ping")
            return True
        except Exception:
            return False

    async def get_account(self) -> dict:
        return await self._request("GET", "/fapi/v2/account", signed=True)

    async def get_balance(self) -> list[dict]:
        account = await self.get_account()
        return [a for a in account.get("assets", []) if float(a.get("walletBalance", 0)) > 0]

    async def get_positions(self) -> list[dict]:
        # /fapi/v2/positionRisk includes markPrice, unRealizedProfit, percentage (ROE%)
        # /fapi/v2/account positions array lacks those fields
        data = await self._request("GET", "/fapi/v2/positionRisk", signed=True)
        positions = [p for p in data if float(p.get("positionAmt", 0)) != 0]
        # Testnet omits percentage; compute ROE% = unrealizedPnl / initialMargin * 100
        for p in positions:
            if "percentage" not in p or p["percentage"] is None:
                try:
                    amt = abs(float(p.get("positionAmt", 0)))
                    entry = float(p.get("entryPrice", 0))
                    leverage = float(p.get("leverage", 1))
                    upnl = float(p.get("unRealizedProfit", 0))
                    initial_margin = (amt * entry) / leverage
                    p["percentage"] = str(round((upnl / initial_margin) * 100, 4)) if initial_margin else "0"
                except (ZeroDivisionError, ValueError):
                    p["percentage"] = "0"
        return positions

    async def place_order(self, **params) -> dict:
        logger.info(f"Placing order: {params.get('symbol')} {params.get('side')} {params.get('type')} qty={params.get('quantity')}")
        result = await self._request("POST", "/fapi/v1/order", params=params, signed=True)
        logger.info(f"Order placed: orderId={result.get('orderId')} status={result.get('status')}")
        return result

    async def get_order(self, symbol: str, order_id: int) -> dict:
        return await self._request(
            "GET", "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    async def get_open_orders(self, symbol: Optional[str] = None) -> list:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

    async def get_ticker_price(self, symbol: str) -> dict:
        return await self._request("GET", "/fapi/v1/ticker/price", params={"symbol": symbol})

    async def get_24hr_ticker(self, symbol: str) -> dict:
        return await self._request("GET", "/fapi/v1/ticker/24hr", params={"symbol": symbol})


# ── Singleton ─────────────────────────────────────────────────────────────────

_binance_client: BinanceFuturesClient | None = None


def get_binance_client() -> BinanceFuturesClient:
    global _binance_client
    if _binance_client is None:
        _binance_client = BinanceFuturesClient()
    return _binance_client


async def close_binance_client() -> None:
    global _binance_client
    if _binance_client:
        await _binance_client.close()
        _binance_client = None
