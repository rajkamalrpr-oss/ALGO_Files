# Binance Futures Trading Bot — Full Stack

A production-structured monorepo trading bot for **Binance USDT-M Futures Testnet** with:

- **React + TypeScript + Vite** frontend (dark terminal aesthetic)
- **FastAPI** async Python backend
- **MongoDB** order persistence via Motor
- **Docker Compose** for one-command startup

---

## Architecture

```
trading-bot/
├── frontend/                  # React + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── api/client.ts      # Axios API layer
│   │   ├── components/        # Sidebar, StatusBadge
│   │   ├── pages/             # Dashboard, Trade, Orders, Account, Analytics
│   │   └── types/             # Shared TypeScript types
│   ├── Dockerfile
│   └── nginx.conf             # SPA routing + API proxy
│
├── backend/                   # FastAPI + Motor + httpx
│   ├── app/
│   │   ├── api/               # FastAPI routers (orders, account)
│   │   ├── core/              # Config (pydantic-settings), Logging
│   │   ├── db/                # MongoDB async connection (Motor)
│   │   ├── models/            # Pydantic models (request, response, DB)
│   │   └── services/          # Binance client, order business logic
│   ├── logs/                  # JSON rotating log file
│   └── Dockerfile
│
└── docker-compose.yml         # mongo + backend + frontend
```

---

## Features

| Feature | Details |
|---|---|
| Order types | `MARKET`, `LIMIT`, `STOP_MARKET` |
| Order sides | `BUY` and `SELL` |
| Time-in-Force | `GTC`, `IOC`, `FOK` (LIMIT only) |
| Persistence | All orders saved to MongoDB after placement |
| Dashboard | KPIs, recent orders, connection status |
| Order history | Paginated table, filterable by symbol |
| Account page | Wallet balances + open positions |
| Analytics | P&L summary, bar chart, pie chart, symbol breakdown |
| Logging | Rotating JSON log file + coloured console |
| Error handling | Typed exceptions: API / Auth / Network |

---

## Quick Start — Docker (recommended)

### Prerequisites
- Docker Desktop (or Docker Engine + Compose)
- A Binance Futures Testnet account

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading-bot
```

### 2. Set up your API credentials

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
BINANCE_TESTNET=true
BINANCE_BASE_URL=https://testnet.binancefuture.com
MONGODB_URL=mongodb://mongo:27017
MONGODB_DB=trading_bot
```

### 3. Start everything

```bash
docker-compose up --build
```

| Service  | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MongoDB | localhost:27017 |

---

## Quick Start — Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and edit env
cp .env.example .env

# Start MongoDB locally or point MONGODB_URL to your instance
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
```

> The Vite dev server proxies `/api` to `http://localhost:8000` automatically.

---

## API Reference

### Orders

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/orders/` | Place a new order |
| `GET` | `/api/v1/orders/` | List order history (filterable, paginated) |
| `GET` | `/api/v1/orders/stats/pnl` | P&L aggregate stats |

**Place order request body:**

```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 0.001
}
```

```json
{
  "symbol": "ETHUSDT",
  "side": "SELL",
  "type": "LIMIT",
  "quantity": 0.01,
  "price": 3500,
  "time_in_force": "GTC"
}
```

```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "type": "STOP_MARKET",
  "quantity": 0.001,
  "stop_price": 65000
}
```

### Account

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/account/balance` | Wallet balances |
| `GET` | `/api/v1/account/positions` | Open positions |
| `GET` | `/api/v1/account/ticker/{symbol}` | 24h ticker |
| `GET` | `/api/v1/account/ping` | Binance connectivity check |

Full interactive docs: **http://localhost:8000/docs**

---

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| Dashboard | `/` | KPI cards, recent orders, quick actions |
| Place Order | `/trade` | BUY/SELL form for all order types |
| Order History | `/orders` | Paginated table with symbol filter |
| Account | `/account` | Balances + open positions |
| Analytics | `/analytics` | P&L, bar chart, pie chart, symbol breakdown |

---

## MongoDB Schema

Each placed order is stored in the `orders` collection:

```json
{
  "_id": "ObjectId",
  "order_id": 3865948231,
  "client_order_id": "x-Cb7ytekJ...",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "MARKET",
  "status": "FILLED",
  "price": 0,
  "orig_qty": 0.001,
  "executed_qty": 0.001,
  "avg_price": 67432.1,
  "time_in_force": "GTC",
  "created_at": "2025-06-04T08:12:01.703Z",
  "raw_response": { ... }
}
```

---

## Logging

Logs are written to `backend/logs/trading_bot.log` as JSON (one record per line):

```json
{"timestamp":"2025-06-04T08:12:01+00:00","level":"INFO","logger":"trading_bot.orders","message":"Order request [MARKET]: {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '0.001'}"}
{"timestamp":"2025-06-04T08:12:01+00:00","level":"INFO","logger":"trading_bot.orders","message":"Order response: orderId=3865948231 status=FILLED executedQty=0.001 avgPrice=67432.10"}
```

Log files rotate at 5 MB (3 backups kept).

---

## Assumptions

- **Testnet only by default.** Set `BINANCE_TESTNET=false` and update `BINANCE_BASE_URL` to switch to mainnet (real funds).
- **One-Way position mode** assumed (Binance default). Hedge mode is not configured.
- **Quantity precision** — values are passed as provided. Binance enforces `stepSize` precision per symbol; refer to exchange info if you get filter errors.
- **No WebSocket** — price data and order status are fetched on-demand via REST. Add a WebSocket connection for live streaming if needed.
- Credentials are loaded from environment variables / `.env` file — never hardcoded.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router |
| Backend | Python 3.12, FastAPI, Uvicorn, Motor (async MongoDB driver) |
| Database | MongoDB 7 |
| HTTP client (BE) | httpx (async) |
| Auth | HMAC-SHA256 signed requests |
| Container | Docker, Docker Compose, Nginx |

---

## License

MIT
