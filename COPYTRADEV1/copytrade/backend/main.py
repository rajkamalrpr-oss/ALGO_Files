"""
CopyTrade Backend — Flat Trade (Master) → Multi-Broker (Follower)
- Master: always Flat Trade WebSocket, connected via daily token
- Follower: pluggable broker — Flat Trade, Zerodha, Angel One, Upstox, Fyers
- Config stored in MongoDB, editable via /api/config
"""

import asyncio
import hashlib
import json
import logging
from collections import deque
from datetime import datetime
from typing import List, Optional

import requests
import websockets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "copytrade"

FT_WS_URL      = "wss://piconnect.flattrade.in/PiConnectWSTp/"
FT_PLACE_ORDER = "https://piconnect.flattrade.in/PiConnectTP/placeorder"

DEFAULT_CONFIG = {
    # Master (always Flat Trade — same token Tradetron uses)
    "master_user":  "",
    "master_token": "",

    # Follower
    "follower_broker":     "flattrade",   # flattrade | zerodha | angelone | upstox | fyers | jainamxts
    "follower_user":       "",
    "follower_api_key":    "",
    "follower_api_secret": "",
    "follower_token":      "",
    "follower_base_url":   "",            # used by Jainam XTS (e.g. https://jainam.xts.in)

    # Postback / tunnel
    "postback_base_url":    "",   # e.g. https://happy-snakes-glow.loca.lt  (leave blank to use public IP)

    # Trading
    "lot_multiplier":       1.0,
    # Follower order price mode:
    #   "always_market"     → always place MARKET on follower (fastest fill, some slippage)
    #   "limit_with_buffer" → LIMIT at master fill price ± buffer% (default, SEBI-safe)
    #   "mirror"            → copy exact price type/price from master (risky: stale price)
    "follower_price_mode":  "limit_with_buffer",
    "price_buffer_pct":     2.0,   # % buffer added to limit price in trade direction
    "tick_size":            0.05,  # NSE F&O default; change to 0.25 for MCX crude etc.
}

app = FastAPI(title="CopyTrade API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo   = MongoClient(MONGO_URI)
db      = mongo[DB_NAME]
col     = db["trades"]
cfg_col = db["config"]

ws_clients: List[WebSocket] = []
master_ws_connected = False
_ws_task: Optional[asyncio.Task] = None

# Ring buffer — last 60 raw messages from Flat Trade WS (for /api/debug)
_ws_raw_log: deque = deque(maxlen=60)
_ws_last_error: str = ""
_last_postback_at: str = ""


# ─── Config ───────────────────────────────────────────────────────

def load_config() -> dict:
    cfg = cfg_col.find_one({}, {"_id": 0})
    if not cfg:
        cfg_col.insert_one({**DEFAULT_CONFIG})
        return {**DEFAULT_CONFIG}
    # Fill any new keys added since last save
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


def save_config(data: dict):
    cfg_col.update_one({}, {"$set": data}, upsert=True)


# ─── Broadcast ────────────────────────────────────────────────────

async def broadcast(data: dict):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in ws_clients:
            ws_clients.remove(ws)


# ─── Price computation (central, used by all brokers) ────────────

def _round_tick(price: float, tick: float) -> float:
    """Round price to nearest valid tick size and 2 decimal places."""
    if tick <= 0:
        tick = 0.05
    return round(round(price / tick) * tick, 2)


def compute_follower_price(order: dict, cfg: dict) -> tuple:
    """
    Returns (is_market: bool, limit_price: float) for the follower order.

    Modes (follower_price_mode):
      "always_market"     — always MARKET regardless of master order type
      "limit_with_buffer" — LIMIT at master fill ± buffer% in trade direction
                            (default; stays within SEBI/exchange dynamic circuit bands)
      "mirror"            — copy exact price type + price from master
                            (risky: stale fill price can breach circuit or not fill)
    """
    mode       = cfg.get("follower_price_mode", "limit_with_buffer")
    buffer_pct = float(cfg.get("price_buffer_pct", 2.0)) / 100.0
    tick       = float(cfg.get("tick_size", 0.05))

    master_prctyp  = order.get("prctyp", "MKT").upper()
    master_is_mkt  = master_prctyp in ("MKT", "MARKET")
    fill_price     = float(order.get("avgprc") or order.get("prc") or 0)
    trantype       = order.get("trantype", "B").upper()

    if mode == "always_market":
        return True, 0.0

    if mode == "mirror":
        return master_is_mkt, (0.0 if master_is_mkt else fill_price)

    # --- "limit_with_buffer" (default) ---
    if master_is_mkt:
        # Master was market → follower also market (exchange price-protects it)
        return True, 0.0

    # Master was limit: add buffer in direction of trade to ensure execution
    # BUY  → cap is HIGHER  (willing to pay up to fill + buffer)
    # SELL → floor is LOWER (willing to accept down to fill - buffer)
    if trantype == "B":
        raw = fill_price * (1 + buffer_pct)
    else:
        raw = fill_price * (1 - buffer_pct)

    limit_price = _round_tick(raw, tick)
    logger.info(
        f"Price: master_fill={fill_price} mode={mode} buffer={buffer_pct*100}% "
        f"tick={tick} → follower_limit={limit_price}"
    )
    return False, limit_price


# ─── Broker order placement ───────────────────────────────────────

def _qty(order: dict, cfg: dict) -> int:
    raw = float(order.get("fillshares") or order.get("qty") or 0)
    return int(raw * float(cfg.get("lot_multiplier", 1.0)))


def _place_flattrade(order: dict, cfg: dict) -> dict:
    is_mkt, price = compute_follower_price(order, cfg)
    jdata = {
        "uid":      cfg["follower_user"],
        "actid":    cfg["follower_user"],
        "exch":     order.get("exch", "NFO"),
        "tsym":     order.get("tsym", ""),
        "qty":      str(_qty(order, cfg)),
        "prd":      order.get("prd", "I"),
        "trantype": order.get("trantype", "B"),
        "prctyp":   "MKT" if is_mkt else "LMT",
        "prc":      "0" if is_mkt else str(price),
        "ret":      "DAY",
        "remarks":  "copytrade",
    }
    try:
        resp = requests.post(
            FT_PLACE_ORDER,
            data={"jData": json.dumps(jdata), "jKey": cfg["follower_token"]},
            timeout=5,
        )
        return resp.json()
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}


def _place_zerodha(order: dict, cfg: dict) -> dict:
    is_mkt, price = compute_follower_price(order, cfg)
    trantype = order.get("trantype", "B")
    try:
        resp = requests.post(
            "https://api.kite.trade/orders/regular",
            headers={
                "X-Kite-Version": "3",
                "Authorization": f"token {cfg['follower_api_key']}:{cfg['follower_token']}",
            },
            data={
                "tradingsymbol":    order.get("tsym", ""),
                "exchange":         order.get("exch", "NFO"),
                "transaction_type": "BUY" if trantype == "B" else "SELL",
                "order_type":       "MARKET" if is_mkt else "LIMIT",
                "quantity":         _qty(order, cfg),
                "price":            0 if is_mkt else price,
                "product":          "MIS",
                "validity":         "DAY",
                "tag":              "copytrade",
            },
            timeout=5,
        )
        r = resp.json()
        if r.get("status") == "success":
            return {"stat": "Ok", "norenordno": r.get("data", {}).get("order_id")}
        return {"stat": "Not_Ok", "emsg": r.get("message", "Unknown error")}
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}


def _place_angelone(order: dict, cfg: dict) -> dict:
    is_mkt, price = compute_follower_price(order, cfg)
    trantype = order.get("trantype", "B")
    try:
        resp = requests.post(
            "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/placeOrder",
            headers={
                "Authorization":   f"Bearer {cfg['follower_token']}",
                "Content-Type":    "application/json",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP":"127.0.0.1",
                "X-MACAddress":    "00:00:00:00:00:00",
                "X-PrivateKey":    cfg["follower_api_key"],
            },
            json={
                "variety":         "NORMAL",
                "tradingsymbol":   order.get("tsym", ""),
                "symboltoken":     "",
                "transactiontype": "BUY" if trantype == "B" else "SELL",
                "exchange":        order.get("exch", "NFO"),
                "ordertype":       "MARKET" if is_mkt else "LIMIT",
                "producttype":     "INTRADAY",
                "duration":        "DAY",
                "price":           "0" if is_mkt else str(price),
                "quantity":        str(_qty(order, cfg)),
                "squareoff":       "0",
                "stoploss":        "0",
            },
            timeout=5,
        )
        r = resp.json()
        if r.get("status"):
            return {"stat": "Ok", "norenordno": r.get("data", {}).get("orderid")}
        return {"stat": "Not_Ok", "emsg": r.get("message", "Unknown error")}
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}


def _place_upstox(order: dict, cfg: dict) -> dict:
    is_mkt, price = compute_follower_price(order, cfg)
    trantype = order.get("trantype", "B")
    try:
        resp = requests.post(
            "https://api.upstox.com/v2/order/place",
            headers={
                "Authorization": f"Bearer {cfg['follower_token']}",
                "Content-Type":  "application/json",
            },
            json={
                "quantity":           _qty(order, cfg),
                "product":            "I",
                "validity":           "DAY",
                "price":              0 if is_mkt else price,
                "tag":                "copytrade",
                "instrument_token":   order.get("tsym", ""),
                "order_type":         "MARKET" if is_mkt else "LIMIT",
                "transaction_type":   "BUY" if trantype == "B" else "SELL",
                "disclosed_quantity": 0,
                "trigger_price":      0,
                "is_amo":             False,
            },
            timeout=5,
        )
        r = resp.json()
        if r.get("status") == "success":
            return {"stat": "Ok", "norenordno": r.get("data", {}).get("order_id")}
        return {"stat": "Not_Ok", "emsg": r.get("errors", [{}])[0].get("message", "Unknown error")}
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}


def _place_fyers(order: dict, cfg: dict) -> dict:
    is_mkt, price = compute_follower_price(order, cfg)
    trantype = order.get("trantype", "B")
    try:
        resp = requests.post(
            "https://api-t1.fyers.in/api/v3/orders/sync",
            headers={
                "Authorization": f"{cfg['follower_api_key']}:{cfg['follower_token']}",
                "Content-Type":  "application/json",
            },
            json={
                "symbol":       f"{order.get('exch', 'NSE')}:{order.get('tsym', '')}",
                "qty":          _qty(order, cfg),
                "type":         2 if is_mkt else 1,   # 2=MARKET, 1=LIMIT
                "side":         1 if trantype == "B" else -1,
                "productType":  "INTRADAY",
                "limitPrice":   0 if is_mkt else price,   # fixed: was always sending fill price
                "stopPrice":    0,
                "validity":     "DAY",
                "filledQty":    0,
                "disclosedQty": 0,
                "offlineOrder": False,
            },
            timeout=5,
        )
        r = resp.json()
        if r.get("s") == "ok":
            return {"stat": "Ok", "norenordno": r.get("id")}
        return {"stat": "Not_Ok", "emsg": r.get("message", "Unknown error")}
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}


XTS_EXCHANGE_MAP = {
    "NSE": "NSECM",
    "NFO": "NSEFO",
    "BSE": "BSECM",
    "BFO": "BSEFO",
    "MCX": "MCXFO",
    "CDS": "NSECD",
}

# Cache: symbol → XTS exchangeInstrumentID, populated on first lookup
_xts_instrument_cache: dict = {}


def _xts_get_instrument_id(base_url: str, token: str, exch: str, tsym: str) -> Optional[int]:
    """Look up the XTS numeric instrument ID for a given symbol."""
    cache_key = f"{exch}:{tsym}"
    if cache_key in _xts_instrument_cache:
        return _xts_instrument_cache[cache_key]

    segment = XTS_EXCHANGE_MAP.get(exch, "NSEFO")
    try:
        resp = requests.get(
            f"{base_url}/interactive/instruments",
            headers={"authorization": token},
            params={"exchangeSegment": segment, "series": "OPTIDX,FUTSTK,FUTIDX,OPTSTK", "symbol": tsym},
            timeout=5,
        )
        result = resp.json()
        instruments = result.get("result", [])
        for inst in instruments:
            if inst.get("tradingSymbol", "").startswith(tsym):
                iid = inst.get("exchangeInstrumentID")
                _xts_instrument_cache[cache_key] = iid
                return iid
    except Exception as e:
        logger.warning(f"XTS instrument lookup failed for {tsym}: {e}")
    return None


def _place_jainamxts(order: dict, cfg: dict) -> dict:
    base_url = cfg.get("follower_base_url", "").rstrip("/")
    token    = cfg.get("follower_token", "")
    if not base_url:
        return {"stat": "Not_Ok", "emsg": "Jainam XTS base URL not configured."}

    is_mkt, price = compute_follower_price(order, cfg)
    trantype      = order.get("trantype", "B")
    exch          = order.get("exch", "NFO")
    tsym          = order.get("tsym", "")
    segment       = XTS_EXCHANGE_MAP.get(exch, "NSEFO")

    instrument_id = _xts_get_instrument_id(base_url, token, exch, tsym)
    if instrument_id is None:
        return {"stat": "Not_Ok", "emsg": f"Could not resolve XTS instrument ID for {exch}:{tsym}"}

    try:
        resp = requests.post(
            f"{base_url}/interactive/orders",
            headers={"authorization": token, "Content-Type": "application/json"},
            json={
                "exchangeSegment":       segment,
                "exchangeInstrumentID":  instrument_id,
                "productType":           "MIS",
                "orderType":             "MARKET" if is_mkt else "LIMIT",
                "orderSide":             "BUY" if trantype == "B" else "SELL",
                "timeInForce":           "DAY",
                "disclosedQuantity":     0,
                "orderQuantity":         _qty(order, cfg),
                "limitPrice":            0 if is_mkt else price,
                "stopPrice":             0,
                "orderUniqueIdentifier": "copytrade",
            },
            timeout=5,
        )
        r = resp.json()
        if r.get("type") == "success":
            app_order_id = r.get("result", {}).get("AppOrderID")
            return {"stat": "Ok", "norenordno": str(app_order_id)}
        return {"stat": "Not_Ok", "emsg": r.get("description", "Unknown XTS error")}
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}


BROKER_HANDLERS = {
    "flattrade": _place_flattrade,
    "zerodha":   _place_zerodha,
    "angelone":  _place_angelone,
    "upstox":    _place_upstox,
    "fyers":     _place_fyers,
    "jainamxts": _place_jainamxts,
}


def place_follower_order(order: dict, cfg: dict) -> dict:
    broker  = cfg.get("follower_broker", "flattrade")
    handler = BROKER_HANDLERS.get(broker)
    if not handler:
        return {"stat": "Not_Ok", "emsg": f"Unknown broker: {broker}"}
    return handler(order, cfg)


# ─── Order handler ────────────────────────────────────────────────

async def handle_order(order: dict, cfg: dict):
    status   = order.get("status", "").upper()
    order_id = order.get("norenordno", "-")
    symbol   = order.get("tsym", "-")
    trantype = order.get("trantype", "-")
    qty      = order.get("fillshares", order.get("qty", "0"))
    price    = order.get("avgprc", order.get("prc", "0"))

    logger.info(
        f"MASTER ORDER → status={status!r} | {'BUY' if trantype == 'B' else 'SELL'} "
        f"{symbol} Qty:{qty} Price:{price} #{order_id}"
    )

    if status != "COMPLETE":
        logger.info(f"  ↳ skipping (status is {status!r}, waiting for COMPLETE)")
        return

    follower_configured = bool(cfg.get("follower_token") and cfg.get("follower_user") or cfg.get("follower_api_key"))

    if not follower_configured:
        # Master-only mode: log the order but skip copying
        event = {
            "master_order_id":   order_id,
            "symbol":            symbol,
            "exchange":          order.get("exch", "-"),
            "action":            "BUY" if trantype == "B" else "SELL",
            "qty":               int(float(qty)),
            "price":             float(price),
            "product":           order.get("prd", "-"),
            "price_type":        order.get("prctyp", "-"),
            "master_status":     status,
            "follower_broker":   cfg.get("follower_broker", "—"),
            "follower_order_id": None,
            "follower_status":   "SKIPPED",
            "follower_message":  "Follower not configured",
            "timestamp":         datetime.now().isoformat(),
        }
        col.insert_one({**event})
        await broadcast({"type": "trade", "data": event})
        logger.info(f"ORDER RECEIVED (copy skipped — follower not configured): {symbol} {trantype} Qty:{qty}")
        return

    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, place_follower_order, order, cfg)

    ok  = result.get("stat") == "Ok"
    oid = result.get("norenordno")
    msg = result.get("emsg", "Success" if ok else "Unknown error")

    event = {
        "master_order_id":   order_id,
        "symbol":            symbol,
        "exchange":          order.get("exch", "-"),
        "action":            "BUY" if trantype == "B" else "SELL",
        "qty":               int(float(qty)),
        "price":             float(price),
        "product":           order.get("prd", "-"),
        "price_type":        order.get("prctyp", "-"),
        "master_status":     status,
        "follower_broker":   cfg.get("follower_broker", "flattrade"),
        "follower_order_id": oid,
        "follower_status":   "SUCCESS" if ok else "FAILED",
        "follower_message":  msg,
        "timestamp":         datetime.now().isoformat(),
    }

    col.insert_one({**event})
    await broadcast({"type": "trade", "data": event})
    logger.info(f"FOLLOWER ({cfg.get('follower_broker')}): {'SUCCESS ✅' if ok else 'FAILED ❌'} | {msg}")


# ─── Flat Trade Master WebSocket loop ────────────────────────────

async def flat_trade_ws_loop():
    global master_ws_connected, _ws_last_error

    while True:
        cfg          = load_config()
        master_user  = cfg.get("master_user", "")
        master_token = cfg.get("master_token", "")

        if not master_user or not master_token:
            logger.warning("Master credentials not set — waiting 10s")
            await asyncio.sleep(10)
            continue

        connect_msg = json.dumps({
            "t":          "c",
            "uid":        master_user,
            "actid":      master_user,
            "source":     "API",
            "susertoken": master_token,
        })

        try:
            logger.info(f"Connecting to Flat Trade WS [{master_user}]...")
            async with websockets.connect(FT_WS_URL, ping_interval=30, ping_timeout=10) as ws:
                await ws.send(connect_msg)
                async for raw in ws:
                    recv_at = datetime.now().isoformat()

                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        _ws_raw_log.append({"at": recv_at, "raw": raw[:300], "parsed": False})
                        logger.warning(f"FT WS non-JSON: {raw[:200]}")
                        continue

                    t = msg.get("t", "?")

                    # Log every message to the ring buffer
                    _ws_raw_log.append({"at": recv_at, "t": t, "msg": msg})
                    logger.info(f"FT WS ← type={t!r} | {json.dumps(msg)[:250]}")

                    if t == "ck":
                        if msg.get("s") == "OK":
                            master_ws_connected = True
                            _ws_last_error = ""
                            logger.info("Flat Trade WS authenticated ✅  — order updates active")
                            await broadcast({"type": "status", "data": {"master_ws": "connected"}})
                        else:
                            err = f"Auth FAILED — Flat Trade rejected token: {msg}"
                            _ws_last_error = err
                            _ws_raw_log.append({"at": datetime.now().isoformat(), "t": "ERROR", "msg": {"error": err}})
                            logger.error(err)
                            await asyncio.sleep(10)
                            break

                    elif t == "om":
                        await handle_order(msg, load_config())

                    else:
                        # Heartbeat / feed / other — already logged above
                        pass

        except asyncio.CancelledError:
            master_ws_connected = False
            logger.info("WS task cancelled (config reload)")
            return
        except Exception as e:
            master_ws_connected = False
            err_str = str(e)
            _ws_last_error = f"Connection error: {err_str}"
            _ws_raw_log.append({"at": datetime.now().isoformat(), "t": "ERROR", "msg": {
                "error": _ws_last_error,
                "hint": "Check IP whitelist in Flat Trade developer portal if this is a connection refused / OSError",
            }})
            await broadcast({"type": "status", "data": {"master_ws": "disconnected"}})
            logger.warning(f"FT WS error ({err_str}) — retrying in 5s")
            await asyncio.sleep(5)


async def restart_ws():
    global _ws_task, master_ws_connected
    if _ws_task and not _ws_task.done():
        _ws_task.cancel()
        try:
            await _ws_task
        except asyncio.CancelledError:
            pass
    master_ws_connected = False
    _ws_task = asyncio.create_task(flat_trade_ws_loop())


# ─── REST endpoints ───────────────────────────────────────────────

class ConfigIn(BaseModel):
    master_user:          str   = ""
    master_token:         str   = ""
    follower_broker:      str   = "flattrade"
    follower_user:        str   = ""
    follower_api_key:     str   = ""
    follower_api_secret:  str   = ""
    follower_token:       str   = ""
    follower_base_url:    str   = ""
    postback_base_url:    str   = ""
    lot_multiplier:       float = 1.0
    follower_price_mode:  str   = "limit_with_buffer"
    price_buffer_pct:     float = 2.0
    tick_size:            float = 0.05


@app.post("/api/generate-master-token")
def generate_master_token(body: dict):
    """
    Log in to Flat Trade and return the susertoken.
    Password and TOTP are NOT stored — only the resulting susertoken is returned.
    """
    uid        = (body.get("uid") or "").strip()
    password   = (body.get("password") or "").strip()
    pan        = (body.get("pan") or "").strip()
    totp       = (body.get("totp") or "").strip()
    api_key    = (body.get("api_key") or "").strip()
    api_secret = (body.get("api_secret") or "").strip()

    if not all([uid, password, api_key, api_secret]):
        return {"stat": "Not_Ok", "emsg": "uid, password, api_key and api_secret are required."}

    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    app_hash = hashlib.sha256(f"{uid}|{api_secret}".encode()).hexdigest()

    # factor2: TOTP takes priority; fall back to PAN if no TOTP configured
    factor2 = totp if totp else pan

    jdata = {
        "uid":     uid,
        "pwd":     pwd_hash,
        "factor2": factor2,
        "vc":      api_key,
        "appkey":  app_hash,
        "imei":    "api",
        "source":  "API",
    }
    try:
        resp = requests.post(
            "https://piconnect.flattrade.in/PiConnectTP/QuickAuth",
            data={"jData": json.dumps(jdata), "jKey": ""},
            timeout=10,
        )
        result = resp.json()
        logger.info(f"FT login response: {result.get('stat')} | {result.get('emsg', '')}")
        if result.get("stat") == "Ok":
            return {"stat": "Ok", "susertoken": result.get("susertoken", "")}
        return {"stat": "Not_Ok", "emsg": result.get("emsg", "Login failed — check credentials")}
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": f"Request error: {e}"}


@app.get("/api/config")
def get_config():
    cfg = load_config()
    cfg.pop("_id", None)
    return cfg


@app.post("/api/config")
async def update_config(body: ConfigIn):
    save_config(body.model_dump())
    return {"message": "Config saved."}


@app.get("/api/system-info")
def system_info():
    try:
        ip = requests.get("https://api.ipify.org", timeout=4).text.strip()
    except Exception:
        ip = "unavailable"
    cfg = load_config()
    base = cfg.get("postback_base_url", "").rstrip("/")
    if not base:
        base = f"http://{ip}:8001"
    return {
        "public_ip": ip,
        "postback_url": f"{base}/api/postback/flattrade",
    }


@app.get("/api/trades")
def get_trades(limit: int = 50):
    return list(col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))


@app.get("/api/status")
def get_status():
    cfg = load_config()
    return {
        "master_user":       cfg.get("master_user", ""),
        "follower_user":     cfg.get("follower_user", ""),
        "follower_broker":   cfg.get("follower_broker", "flattrade"),
        "ws_connected":      master_ws_connected,
        "last_postback_at":  _last_postback_at,
        "total_trades":      col.count_documents({}),
        "success_count":     col.count_documents({"follower_status": "SUCCESS"}),
        "failed_count":      col.count_documents({"follower_status": "FAILED"}),
    }


@app.delete("/api/trades")
def clear_trades():
    col.delete_many({})
    return {"message": "Cleared"}


@app.get("/api/debug")
def get_debug():
    """Show last raw WS messages from Flat Trade — use this to diagnose connection issues."""
    messages = list(_ws_raw_log)
    by_type  = {}
    for m in messages:
        t = m.get("t", "non-json")
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "ws_connected":   master_ws_connected,
        "last_error":     _ws_last_error,
        "messages_count": len(messages),
        "by_type":        by_type,
        "last_messages":  messages[-20:],
    }


@app.post("/api/debug/inject")
async def inject_order(payload: dict):
    """
    Inject a fake COMPLETE order to test the full pipeline without placing a real order.
    Example body:
    {
      "tsym": "NIFTY25MAYFUT", "exch": "NFO",
      "trantype": "B", "qty": "50", "prctyp": "MKT",
      "avgprc": "24500.00", "fillshares": "50",
      "prd": "I", "norenordno": "TEST001"
    }
    """
    fake = {
        "t":          "om",
        "status":     "COMPLETE",
        "norenordno": payload.get("norenordno", "TEST001"),
        "tsym":       payload.get("tsym", "NIFTY25MAYFUT"),
        "exch":       payload.get("exch", "NFO"),
        "trantype":   payload.get("trantype", "B"),
        "qty":        payload.get("qty", "50"),
        "fillshares": payload.get("fillshares", payload.get("qty", "50")),
        "avgprc":     payload.get("avgprc", "24500.00"),
        "prctyp":     payload.get("prctyp", "MKT"),
        "prd":        payload.get("prd", "I"),
    }
    _ws_raw_log.append({"at": datetime.now().isoformat(), "t": "om", "msg": fake, "injected": True})
    await handle_order(fake, load_config())
    return {"message": "Injected", "order": fake}


@app.post("/api/postback/flattrade")
async def flattrade_postback(request: Request):
    """
    Flat Trade order postback endpoint.
    Configure in Flat Trade developer portal → API App → Postback URL.
    Flat Trade POSTs order details here (form: jData=<json>) on every order status change.
    No API key or WebSocket needed — Tradetron can keep its own connection undisturbed.
    """
    global _last_postback_at

    content_type = request.headers.get("content-type", "")
    order = None

    try:
        if "application/json" in content_type:
            order = await request.json()
        else:
            # Flat Trade sends: jData=<json_string>&jKey=<api_key>
            form = await request.form()
            jdata_str = form.get("jData") or form.get("jdata")
            if jdata_str:
                order = json.loads(jdata_str)
            else:
                body = await request.body()
                order = json.loads(body)
    except Exception as e:
        logger.warning(f"Postback parse error: {e}")
        return {"status": "error", "reason": str(e)}

    if not order:
        return {"status": "error", "reason": "empty payload"}

    order.setdefault("t", "om")
    _last_postback_at = datetime.now().isoformat()
    _ws_raw_log.append({
        "at": _last_postback_at,
        "t": order.get("t", "om"),
        "msg": order,
        "source": "postback",
    })
    logger.info(f"FT Postback ← {json.dumps(order)[:300]}")

    await handle_order(order, load_config())
    return {"status": "ok"}


@app.post("/api/webhook/tradetron")
async def tradetron_webhook(payload: dict):
    """
    Receives order execution signals from Tradetron.
    Configure in each Tradetron strategy: Actions → Webhook → URL = http://<your-ip>:8001/api/webhook/tradetron
    Tradetron sends fields like: trading_symbol, action (BUY/SELL), quantity, price, exchange, product_type, order_type
    """
    logger.info(f"Tradetron webhook received: {json.dumps(payload)[:300]}")

    # Normalise Tradetron's field names → our internal order format
    # Tradetron typically sends camelCase or snake_case depending on strategy config
    tsym     = (payload.get("trading_symbol") or payload.get("tradingSymbol") or payload.get("symbol") or "").strip()
    exch     = (payload.get("exchange") or payload.get("exch") or "NFO").strip().upper()
    action   = (payload.get("action") or payload.get("transaction_type") or payload.get("transactionType") or "B").strip().upper()
    qty      = str(payload.get("quantity") or payload.get("qty") or 0)
    price    = str(payload.get("price") or payload.get("avg_price") or payload.get("avgprc") or "0")
    prctyp   = (payload.get("order_type") or payload.get("orderType") or payload.get("prctyp") or "MKT").strip().upper()
    prd      = (payload.get("product_type") or payload.get("productType") or payload.get("prd") or "I").strip()
    order_id = str(payload.get("order_id") or payload.get("orderId") or payload.get("norenordno") or f"TT-{datetime.now().strftime('%H%M%S')}").strip()

    # Normalise action: BUY→B, SELL→S
    trantype = "B" if action in ("BUY", "B") else "S"
    # Normalise price type: MARKET→MKT, LIMIT→LMT
    if prctyp in ("MARKET", "MKT"):
        prctyp = "MKT"
    elif prctyp in ("LIMIT", "LMT"):
        prctyp = "LMT"

    if not tsym:
        logger.warning("Tradetron webhook: missing trading_symbol — ignored")
        return {"status": "ignored", "reason": "missing trading_symbol"}

    # Build an order dict that matches our internal handle_order format
    order = {
        "t":          "om",
        "status":     "COMPLETE",
        "norenordno": order_id,
        "tsym":       tsym,
        "exch":       exch,
        "trantype":   trantype,
        "qty":        qty,
        "fillshares": qty,
        "avgprc":     price,
        "prctyp":     prctyp,
        "prd":        prd,
    }

    # Log to the debug ring buffer so it shows in the Debug Panel
    _ws_raw_log.append({"at": datetime.now().isoformat(), "t": "om", "msg": order, "injected": False, "source": "tradetron_webhook"})

    await handle_order(order, load_config())
    return {"status": "ok", "order_id": order_id, "symbol": tsym, "action": trantype, "qty": qty}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        trades = list(col.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
        await websocket.send_json({"type": "init", "data": trades})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in ws_clients:
            ws_clients.remove(websocket)


@app.on_event("startup")
async def startup():
    load_config()
    logger.info("CopyTrade backend started on port 9001.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9001, reload=False)
