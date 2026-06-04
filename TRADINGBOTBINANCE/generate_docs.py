"""
Generates Architecture & Setup document for FuturesBot Trading Application.
Output: FuturesBot_Architecture_Guide.docx
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── Colour palette ────────────────────────────────────────────────────────────
C_NAVY   = RGBColor(0x0F, 0x17, 0x2A)   # headings
C_INDIGO = RGBColor(0x4F, 0x46, 0xE5)   # accent headings
C_GREEN  = RGBColor(0x05, 0x96, 0x69)   # positive / backend
C_ORANGE = RGBColor(0xF7, 0x93, 0x1A)   # BTC orange
C_BLUE   = RGBColor(0x62, 0x7E, 0xEA)   # ETH blue
C_GOLD   = RGBColor(0xF3, 0xBA, 0x2F)   # BNB gold
C_GRAY   = RGBColor(0x64, 0x74, 0x8B)   # body text
C_LGRAY  = RGBColor(0x94, 0xA3, 0xB8)   # muted
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
C_TBLHDR = RGBColor(0x1E, 0x29, 0x3B)   # table header bg

# ── Helpers ───────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)

def add_heading(doc, text, level=1, color=None, space_before=12, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    run = p.add_run(text)
    if level == 1:
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = color or C_NAVY
    elif level == 2:
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = color or C_INDIGO
    elif level == 3:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = color or C_NAVY
    elif level == 4:
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = color or C_GRAY
    return p

def add_para(doc, text, bold=False, italic=False, color=None, size=10.5,
             space_before=2, space_after=4, indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    run.font.color.rgb = color or C_GRAY
    return p

def add_bullet(doc, text, level=0, color=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.left_indent  = Cm(0.6 + level * 0.6)
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.color.rgb = color or C_GRAY

def add_code_block(doc, lines):
    """Renders a monospaced diagram/code block."""
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(0)
        p.paragraph_format.left_indent  = Cm(0.8)
        run = p.add_run(line)
        run.font.name  = 'Courier New'
        run.font.size  = Pt(8.5)
        run.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)

def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    # header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        set_cell_bg(hdr_cells[i], '1E293B')
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        run = hdr_cells[i].paragraphs[0].add_run(h)
        run.font.bold  = True
        run.font.size  = Pt(9)
        run.font.color.rgb = C_WHITE
    # data rows
    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        bg = 'FFFFFF' if ri % 2 == 0 else 'F8FAFC'
        for ci, val in enumerate(row):
            set_cell_bg(cells[ci], bg)
            cells[ci].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            run = cells[ci].paragraphs[0].add_run(str(val))
            run.font.size = Pt(9)
            run.font.color.rgb = C_GRAY
    # column widths
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    return table

def add_divider(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'),   'single')
    bottom.set(qn('w:sz'),    '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'E2E8F0')
    pBdr.append(bottom)
    pPr.append(pBdr)


# ═════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═════════════════════════════════════════════════════════════════════════════

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# Default font
doc.styles['Normal'].font.name = 'Calibri'
doc.styles['Normal'].font.size = Pt(10.5)


# ── TITLE PAGE ────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(60)
p.paragraph_format.space_after  = Pt(4)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('FuturesBot')
r.font.size  = Pt(36)
r.font.bold  = True
r.font.color.rgb = C_NAVY

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
p2.paragraph_format.space_after = Pt(2)
r2 = p2.add_run('Binance USDT-M Futures Trading Bot')
r2.font.size = Pt(18)
r2.font.bold = True
r2.font.color.rgb = C_INDIGO

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run('Architecture, Developer Guide & Installation Manual')
r3.font.size = Pt(12)
r3.font.color.rgb = C_LGRAY

doc.add_paragraph()
p4 = doc.add_paragraph()
p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
r4 = p4.add_run('Version 1.0  ·  Binance Testnet  ·  FastAPI + React + MongoDB')
r4.font.size  = Pt(10)
r4.font.color.rgb = C_LGRAY
r4.font.italic = True

doc.add_page_break()


# ── 1. EXECUTIVE SUMMARY ─────────────────────────────────────────────────────
add_heading(doc, '1. Executive Summary', 1)
add_para(doc,
    'FuturesBot is a full-stack trading bot application that allows users to place, monitor, and manage '
    'orders on the Binance USDT-M Futures Testnet. It provides a clean web-based dashboard for real-time '
    'position tracking, P&L analytics, and automated order-status synchronisation.',
    size=10.5)
add_para(doc,
    'The application is built with a Python/FastAPI backend, a React/TypeScript frontend, and MongoDB '
    'for order persistence. Docker Compose is provided to run all three services in a single command.',
    size=10.5)

add_heading(doc, 'Key Features', 3)
features = [
    'Place MARKET, LIMIT, and STOP_MARKET orders on Binance Futures Testnet',
    'Real-time open position tracking with Mark Price, Unrealised PnL, and ROE%',
    'Automatic 1-second background sync keeps order statuses current',
    'Partial or full position exit via a guided modal with percentage quick-fill',
    'P&L analytics with bar and pie charts (Recharts)',
    'API credential management via the Settings page (persisted to .env)',
    'Full Docker Compose deployment with health checks',
    'Stylised light-theme UI with crypto-themed SVG background art',
]
for f in features:
    add_bullet(doc, f)

add_divider(doc)


# ── 2. TECHNOLOGY STACK ───────────────────────────────────────────────────────
add_heading(doc, '2. Technology Stack', 1)

add_table(doc,
    ['Layer', 'Technology', 'Version', 'Purpose'],
    [
        ['Backend',   'Python',            '3.11+',   'Runtime language'],
        ['Backend',   'FastAPI',           '0.111',   'Async REST framework'],
        ['Backend',   'Uvicorn',           '0.29',    'ASGI server'],
        ['Backend',   'Motor',             '3.4',     'Async MongoDB driver'],
        ['Backend',   'Pydantic v2',       '2.7',     'Request validation & settings'],
        ['Backend',   'httpx',             '0.27',    'Async HTTP client for Binance API'],
        ['Database',  'MongoDB',           '7',       'Order persistence (NoSQL)'],
        ['Frontend',  'React',             '18.3',    'UI library'],
        ['Frontend',  'TypeScript',        '5.4',     'Type-safe JavaScript'],
        ['Frontend',  'Vite',              '5.3',     'Dev server & bundler'],
        ['Frontend',  'Tailwind CSS',      '3.4',     'Utility-first CSS'],
        ['Frontend',  'Recharts',          '2.12',    'Chart components'],
        ['Frontend',  'Axios',             '1.7',     'HTTP client'],
        ['Frontend',  'Lucide React',      '0.383',   'SVG icon set'],
        ['Infra',     'Docker Compose',    '3.9',     'Multi-service orchestration'],
        ['Infra',     'Nginx',             'alpine',  'Static frontend serving'],
    ],
    col_widths=[1.0, 1.5, 0.9, 3.2]
)

add_divider(doc)


# ── 3. HIGH-LEVEL ARCHITECTURE ────────────────────────────────────────────────
add_heading(doc, '3. High-Level Architecture', 1)
add_para(doc,
    'The application follows a classic three-tier architecture: a React single-page application (SPA) '
    'served by Nginx communicates with a FastAPI REST backend, which in turn connects to MongoDB for '
    'persistence and to the Binance Futures API for live market data and order execution.',
    size=10.5)

add_heading(doc, 'Architecture Overview Diagram', 3)
add_code_block(doc, [
    '                                                                           ',
    '  ┌─────────────────────────────────────────────────────────────────────┐ ',
    '  │                        DOCKER COMPOSE NETWORK                       │ ',
    '  │                                                                      │ ',
    '  │  ┌──────────────────┐        ┌──────────────────┐                  │ ',
    '  │  │   FRONTEND        │        │    BACKEND        │                  │ ',
    '  │  │   React + Vite    │◄──────►│    FastAPI        │                  │ ',
    '  │  │   Nginx :80       │  HTTP  │    Uvicorn :8000  │                  │ ',
    '  │  │   Port 3000       │        │    Port 8000      │                  │ ',
    '  │  └──────────────────┘        └────────┬─────────┘                  │ ',
    '  │                                        │                             │ ',
    '  │                           ┌────────────┴──────────┐                 │ ',
    '  │                           │                        │                 │ ',
    '  │                  ┌────────▼─────────┐    ┌────────▼─────────┐      │ ',
    '  │                  │    MONGODB        │    │  BINANCE API      │      │ ',
    '  │                  │    Motor async    │    │  USDT-M Futures   │      │ ',
    '  │                  │    Port 27017     │    │  Testnet HTTPS    │      │ ',
    '  │                  └──────────────────┘    └──────────────────┘      │ ',
    '  └─────────────────────────────────────────────────────────────────────┘ ',
    '                                                                           ',
    '  Browser ──► localhost:3000 (Frontend)                                   ',
    '  Frontend proxies /api/* ──► localhost:8000 (Backend)                    ',
    '  Backend signs & calls ──► testnet.binancefuture.com                     ',
    '                                                                           ',
])

add_divider(doc)


# ── 4. BACKEND ARCHITECTURE ───────────────────────────────────────────────────
add_heading(doc, '4. Backend Architecture', 1)
add_para(doc,
    'The backend is a fully asynchronous FastAPI application. All database queries use the Motor async '
    'driver and all Binance API calls use httpx AsyncClient, meaning requests never block the event loop.',
    size=10.5)

add_heading(doc, 'Module Structure', 3)
add_code_block(doc, [
    'backend/',
    '├── app/',
    '│   ├── main.py              ← FastAPI app, CORS, routers, lifespan',
    '│   ├── api/',
    '│   │   ├── account.py       ← /api/v1/account/* endpoints',
    '│   │   └── orders.py        ← /api/v1/orders/* endpoints',
    '│   ├── services/',
    '│   │   ├── binance.py       ← Async Binance REST client (HMAC signing)',
    '│   │   └── order_service.py ← Order business logic & MongoDB queries',
    '│   ├── models/',
    '│   │   └── order.py         ← Pydantic request/response models & enums',
    '│   ├── db/',
    '│   │   ├── database.py      ← Motor client, connect/close/get helpers',
    '│   │   └── settings_store.py← Bot settings persistence in MongoDB',
    '│   └── core/',
    '│       ├── config.py        ← Pydantic Settings (loads .env)',
    '│       └── logging.py       ← JSON rotating logger',
    '├── requirements.txt',
    '├── Dockerfile',
    '└── .env                     ← API keys & MongoDB URL (not in git)',
])

add_heading(doc, 'Request Lifecycle', 3)
add_code_block(doc, [
    '  Browser / Frontend',
    '       │  HTTP POST /api/v1/orders/',
    '       ▼',
    '  FastAPI Router (orders.py)',
    '       │  validates PlaceOrderRequest via Pydantic',
    '       ▼',
    '  order_service.place_and_store_order()',
    '       │  builds Binance params dict',
    '       ▼',
    '  BinanceFuturesClient.place_order()',
    '       │  signs with HMAC-SHA256, POST /fapi/v1/order',
    '       ▼',
    '  Binance Testnet API  ──►  returns raw order JSON',
    '       │',
    '       ▼',
    '  (MARKET only) re-fetch after 0.4s if status != FILLED',
    '       │',
    '       ▼',
    '  MongoDB insert_one(orders collection)',
    '       │',
    '       ▼',
    '  OrderResponse returned to browser',
])

add_heading(doc, 'Background Sync Loop', 3)
add_para(doc,
    'At startup, a background asyncio task polls every 1 second. It finds all orders with status '
    'NEW or PARTIALLY_FILLED, re-fetches each from Binance, and updates MongoDB if the status, '
    'executed_qty, or avg_price has changed. This ensures LIMIT order fills are reflected within ~1 second.',
    size=10.5)

add_heading(doc, 'API Endpoints Reference', 3)
add_table(doc,
    ['Method', 'Endpoint', 'Description'],
    [
        ['GET',  '/health',                             'Health check'],
        ['GET',  '/api/v1/orders/',                     'List order history (pagination + symbol filter)'],
        ['POST', '/api/v1/orders/',                     'Place a new order (MARKET / LIMIT / STOP_MARKET)'],
        ['GET',  '/api/v1/orders/stats/pnl',            'Aggregated P&L stats (optional ?today=true)'],
        ['POST', '/api/v1/orders/sync',                 'Force sync all NEW/PARTIALLY_FILLED orders'],
        ['GET',  '/api/v1/account/balance',             'Wallet balances (non-zero assets)'],
        ['GET',  '/api/v1/account/positions',           'Open positions with markPrice, UPnL, ROE%'],
        ['POST', '/api/v1/account/positions/{sym}/exit','Exit position (optional ?qty= for partial exit)'],
        ['GET',  '/api/v1/account/ticker/{symbol}',     '24-hour ticker stats'],
        ['GET',  '/api/v1/account/ping',                'Binance API connectivity check'],
        ['GET',  '/api/v1/account/credentials',         'Get masked API key status'],
        ['POST', '/api/v1/account/credentials',         'Update API credentials at runtime'],
    ],
    col_widths=[0.7, 3.3, 2.6]
)

add_divider(doc)


# ── 5. FRONTEND ARCHITECTURE ──────────────────────────────────────────────────
add_heading(doc, '5. Frontend Architecture', 1)
add_para(doc,
    'The frontend is a React 18 single-page application written in TypeScript, bundled by Vite. '
    'Tailwind CSS provides a utility-first styling system. During development, Vite proxies all '
    '/api/* requests to the backend. In production (Docker), Nginx handles static file serving '
    'and proxies /api/* to the backend container.',
    size=10.5)

add_heading(doc, 'Module Structure', 3)
add_code_block(doc, [
    'frontend/src/',
    '├── App.tsx              ← Router, Toaster, Sidebar, BackgroundDecor',
    '├── main.tsx             ← React root mount',
    '├── index.css            ← Tailwind base + custom component classes',
    '├── api/',
    '│   └── client.ts        ← Axios instance, all API helper functions',
    '├── types/',
    '│   └── index.ts         ← TypeScript interfaces (Order, Position, etc.)',
    '├── components/',
    '│   ├── Sidebar.tsx      ← Left navigation (NavLink active highlighting)',
    '│   ├── StatusBadge.tsx  ← Colored status pill for order status',
    '│   └── BackgroundDecor.tsx ← Decorative SVG (BTC/ETH/BNB + hex grid)',
    '└── pages/',
    '    ├── DashboardPage.tsx  ← KPI cards + recent orders + quick actions',
    '    ├── TradePage.tsx      ← Order form (BUY/SELL, order types)',
    '    ├── OrdersPage.tsx     ← Order history table with auto-sync',
    '    ├── AccountPage.tsx    ← Balances + positions + exit modal',
    '    ├── AnalyticsPage.tsx  ← Recharts bar/pie + symbol breakdown table',
    '    └── SettingsPage.tsx   ← API credential management',
])

add_heading(doc, 'Page Summary', 3)
add_table(doc,
    ['Page', 'Route', 'Key Features'],
    [
        ['Dashboard',    '/',           'KPI cards, recent orders, quick-action links, API status indicator'],
        ['Place Order',  '/trade',      'BUY/SELL toggle, symbol, order type, qty/price inputs, result card'],
        ['Order History','/orders',     'Auto-sync on load, symbol filter, pagination (20/page)'],
        ['Account',      '/account',    '1-sec refresh, balances, positions with UPnL/ROE%, exit modal'],
        ['Analytics',    '/analytics',  'Bar chart (qty by symbol), pie chart (orders by symbol), PnL table'],
        ['Settings',     '/settings',   'API key form, show/hide secret, runtime credential update'],
    ],
    col_widths=[1.3, 1.3, 4.0]
)

add_heading(doc, 'Data Flow Diagram', 3)
add_code_block(doc, [
    '  AccountPage                                                               ',
    '      │  useEffect every 1s                                                 ',
    '      │  ┌─────────────────────────────────────────┐                       ',
    '      │  │ Promise.all([                            │                       ',
    '      │  │   fetchBalances()  ──► GET /balance      │                       ',
    '      │  │   fetchPositions() ──► GET /positions    │                       ',
    '      │  │   fetchTodayPnl()  ──► GET /stats/pnl   │                       ',
    '      │  │ ])                                       │                       ',
    '      │  └─────────────────────────────────────────┘                       ',
    '      │                                                                     ',
    '      │  User clicks Exit ──► ExitModal opens                              ',
    '      │  User enters qty / selects 25-100%                                 ',
    '      │  Confirm ──► POST /positions/{symbol}/exit?qty=X                  ',
    '      │           ──► reduceOnly MARKET order placed                       ',
    '      │           ──► order stored in MongoDB                              ',
    '      │           ──► positions refreshed                                  ',
])

add_divider(doc)


# ── 6. DATABASE SCHEMA ────────────────────────────────────────────────────────
add_heading(doc, '6. Database Schema', 1)
add_para(doc,
    'MongoDB is used as the persistence layer. There is currently one main collection: orders.',
    size=10.5)

add_heading(doc, 'orders Collection', 3)
add_table(doc,
    ['Field', 'Type', 'Description'],
    [
        ['_id',             'ObjectId',  'MongoDB auto-generated document ID'],
        ['order_id',        'int',       'Binance order ID'],
        ['client_order_id', 'string',    'Binance client order ID'],
        ['symbol',          'string',    'Trading pair e.g. BTCUSDT'],
        ['side',            'string',    'BUY or SELL'],
        ['order_type',      'string',    'MARKET, LIMIT, or STOP_MARKET'],
        ['status',          'string',    'NEW / PARTIALLY_FILLED / FILLED / CANCELED / REJECTED / EXPIRED'],
        ['price',           'float',     'Limit price (0 for MARKET orders)'],
        ['orig_qty',        'float',     'Original order quantity'],
        ['executed_qty',    'float',     'Quantity filled so far'],
        ['avg_price',       'float',     'Volume-weighted average fill price'],
        ['time_in_force',   'string',    'GTC / IOC / FOK'],
        ['created_at',      'datetime',  'UTC timestamp when stored in MongoDB'],
        ['raw_response',    'object',    'Full raw JSON response from Binance (audit trail)'],
    ],
    col_widths=[1.5, 0.9, 4.2]
)

add_heading(doc, 'Indexes (recommended)', 3)
add_bullet(doc, 'symbol  (for symbol-filtered queries)')
add_bullet(doc, 'status  (for sync loop: find NEW/PARTIALLY_FILLED)')
add_bullet(doc, 'created_at  (for time-based sorting and today filter)')

add_divider(doc)


# ── 7. BINANCE INTEGRATION ────────────────────────────────────────────────────
add_heading(doc, '7. Binance API Integration', 1)
add_para(doc,
    'All communication with Binance uses the USDT-M Futures Testnet REST API. '
    'Every signed request appends a timestamp, a recvWindow (5000ms), and an '
    'HMAC-SHA256 signature of the full query string using the API secret.',
    size=10.5)

add_heading(doc, 'Key Endpoints Used', 3)
add_table(doc,
    ['Binance Endpoint', 'Used For'],
    [
        ['/fapi/v1/ping',         'Connectivity health check'],
        ['/fapi/v2/account',      'Wallet assets (balance endpoint)'],
        ['/fapi/v2/positionRisk', 'Open positions with markPrice, unRealizedProfit, percentage'],
        ['/fapi/v1/order (POST)', 'Place new order'],
        ['/fapi/v1/order (GET)',  'Fetch single order status (used by sync loop)'],
        ['/fapi/v1/openOrders',   'List all open orders'],
        ['/fapi/v1/ticker/price', 'Current price for a symbol'],
        ['/fapi/v1/ticker/24hr',  '24-hour statistics'],
    ],
    col_widths=[2.8, 3.8]
)

add_para(doc,
    'Note: /fapi/v2/positionRisk is used instead of the positions array inside '
    '/fapi/v2/account because only positionRisk includes markPrice and percentage (ROE%). '
    'For the Testnet which omits percentage, ROE% is computed as: '
    'unRealizedProfit / (|positionAmt| × entryPrice / leverage) × 100.',
    italic=True, size=9.5, color=C_LGRAY)

add_divider(doc)


# ── 8. DEPLOYMENT ARCHITECTURE ────────────────────────────────────────────────
add_heading(doc, '8. Docker Deployment Architecture', 1)

add_code_block(doc, [
    '  docker-compose up --build',
    '                                                                     ',
    '  ┌──────────────────────────────────────────────────────────────┐  ',
    '  │                  Docker Compose Network                       │  ',
    '  │                                                               │  ',
    '  │  ┌─────────────────┐    ┌─────────────────┐                 │  ',
    '  │  │   frontend        │    │    backend        │                 │  ',
    '  │  │   Nginx :80       │    │    Uvicorn :8000  │                 │  ',
    '  │  │   Host: 3000      │    │    Host: 8000     │                 │  ',
    '  │  │                   │    │                   │                 │  ',
    '  │  │  static files     │    │  .env (secrets)   │                 │  ',
    '  │  │  nginx.conf       │    │  logs/ (volume)   │                 │  ',
    '  │  └────────┬──────────┘    └──────────┬────────┘                 │  ',
    '  │           │  /api/* proxy             │ mongodb://mongo:27017    │  ',
    '  │           └──────────────►            │                          │  ',
    '  │                                       ▼                          │  ',
    '  │                          ┌─────────────────────┐                │  ',
    '  │                          │       mongo           │                │  ',
    '  │                          │   MongoDB 7 :27017    │                │  ',
    '  │                          │   Volume: mongo_data  │                │  ',
    '  │                          └─────────────────────┘                │  ',
    '  └──────────────────────────────────────────────────────────────────┘  ',
])

add_table(doc,
    ['Service', 'Image / Build', 'Host Port', 'Internal Port', 'Notes'],
    [
        ['frontend', 'Build: ./frontend/Dockerfile', '3000', '80',    'Nginx serves React build, proxies /api/*'],
        ['backend',  'Build: ./backend/Dockerfile',  '8000', '8000',  'FastAPI + Uvicorn, reads .env'],
        ['mongo',    'mongo:7',                       '27017','27017', 'Named volume mongo_data persists data'],
    ],
    col_widths=[1.0, 1.8, 0.9, 1.1, 2.8]
)

add_divider(doc)


# ── 9. INSTALLATION GUIDE ─────────────────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '9. Installation & Setup Guide', 1)
add_para(doc,
    'This section describes how to download and run the FuturesBot application on a fresh machine. '
    'Two methods are provided: Docker (recommended, one command) and Manual (run each service locally).',
    size=10.5)


# 9.1 Prerequisites
add_heading(doc, '9.1  Prerequisites', 2)
add_heading(doc, 'Option A — Docker (Recommended)', 3)
add_table(doc,
    ['Software', 'Minimum Version', 'Download Link'],
    [
        ['Git',            '2.x',    'https://git-scm.com/downloads'],
        ['Docker Desktop', '4.x',    'https://www.docker.com/products/docker-desktop'],
        ['(Docker includes Docker Compose)', '', ''],
    ],
    col_widths=[1.8, 1.5, 3.3]
)

add_heading(doc, 'Option B — Manual (No Docker)', 3)
add_table(doc,
    ['Software', 'Minimum Version', 'Download Link'],
    [
        ['Git',     '2.x',   'https://git-scm.com/downloads'],
        ['Python',  '3.11+', 'https://www.python.org/downloads'],
        ['Node.js', '18+',   'https://nodejs.org/en/download'],
        ['MongoDB', '6+',    'https://www.mongodb.com/try/download/community'],
    ],
    col_widths=[1.3, 1.5, 3.8]
)


# 9.2 Binance Testnet Keys
add_heading(doc, '9.2  Get Binance Testnet API Keys', 2)
add_para(doc, 'You need API keys from the Binance USDT-M Futures Testnet (free, no real money):')
steps = [
    'Open https://testnet.binancefuture.com in your browser.',
    'Log in with your GitHub account (or create a free Binance testnet account).',
    'Click "API Key" in the top navigation bar.',
    'Click "Generate" to create a new key pair.',
    'Copy and save both the API Key and API Secret — the secret is shown only once.',
]
for i, s in enumerate(steps, 1):
    add_bullet(doc, f'Step {i}: {s}')


# 9.3 Download the code
add_heading(doc, '9.3  Download the Code', 2)
add_heading(doc, 'Clone from GitHub', 4)
add_code_block(doc, [
    'git clone https://github.com/rajkamalrpr-oss/ALGO_Files.git',
    'cd ALGO_Files/TRADINGBOTBINANCE/trading-bot-complete/trading-bot',
])
add_para(doc, 'All commands below assume you are inside this trading-bot/ directory.', italic=True, color=C_LGRAY)


# 9.4 Configure .env
add_heading(doc, '9.4  Configure Environment Variables', 2)
add_code_block(doc, [
    '# From the trading-bot/ directory:',
    'cp backend/.env.example backend/.env',
    '',
    '# Open backend/.env in any text editor and fill in your keys:',
    'BINANCE_API_KEY=<paste your testnet API key here>',
    'BINANCE_API_SECRET=<paste your testnet API secret here>',
    'BINANCE_TESTNET=true',
    'BINANCE_BASE_URL=https://testnet.binancefuture.com',
    'MONGODB_URL=mongodb://mongo:27017',
    'MONGODB_DB=trading_bot',
    'APP_ENV=development',
    'LOG_LEVEL=DEBUG',
])


# 9.5 Docker method
add_heading(doc, '9.5  Running with Docker (Recommended)', 2)
add_para(doc, 'After completing steps 9.3 and 9.4, run:', bold=True)
add_code_block(doc, [
    '# Start all three services (MongoDB, Backend, Frontend):',
    'docker compose up --build',
    '',
    '# To run in the background:',
    'docker compose up --build -d',
    '',
    '# To stop all services:',
    'docker compose down',
    '',
    '# To stop and delete all data (MongoDB volume):',
    'docker compose down -v',
])
add_para(doc, 'Once started, open http://localhost:3000 in your browser.', bold=True, color=C_GREEN)

add_heading(doc, 'Verify services are running', 4)
add_code_block(doc, [
    'docker compose ps',
    '',
    '# You should see:',
    '#  trading_bot_mongo     mongo:7        Up (healthy)',
    '#  trading_bot_backend   ...backend     Up',
    '#  trading_bot_frontend  ...frontend    Up',
])


# 9.6 Manual method
add_heading(doc, '9.6  Running Manually (Without Docker)', 2)
add_heading(doc, 'Step 1 — Start MongoDB', 3)
add_code_block(doc, [
    '# Windows (if MongoDB is installed as a service, it may already be running)',
    'net start MongoDB',
    '',
    '# Mac/Linux',
    'brew services start mongodb-community   # Homebrew',
    '# OR',
    'sudo systemctl start mongod             # systemd',
])

add_heading(doc, 'Step 2 — Set up & Start the Backend', 3)
add_code_block(doc, [
    'cd backend',
    '',
    '# Create a Python virtual environment',
    'python -m venv venv',
    '',
    '# Activate it',
    'venv\\Scripts\\activate          # Windows',
    'source venv/bin/activate         # Mac / Linux',
    '',
    '# Install dependencies',
    'pip install -r requirements.txt',
    '',
    '# Edit .env (if not done in step 9.4)',
    '# Set MONGODB_URL=mongodb://localhost:27017  (local MongoDB, not Docker)',
    '',
    '# Start the backend',
    'uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload',
    '',
    '# Verify: open http://localhost:8000/health  → should return {"status":"healthy"}',
])

add_heading(doc, 'Step 3 — Set up & Start the Frontend', 3)
add_code_block(doc, [
    'cd ../frontend',
    '',
    '# Install Node.js dependencies',
    'npm install',
    '',
    '# Start the Vite dev server (proxies /api/* to localhost:8000)',
    'npm run dev',
    '',
    '# Open http://localhost:3000 in your browser',
])

add_heading(doc, 'Step 4 — Build for Production (optional)', 3)
add_code_block(doc, [
    '# Inside frontend/',
    'npm run build',
    '# Creates frontend/dist/ — serve with any static file server',
])


# 9.7 First run checklist
add_heading(doc, '9.7  First-Run Checklist', 2)
checklist = [
    ('Open http://localhost:3000',                          'Should see the FuturesBot Dashboard'),
    ('Dashboard → API status dot (top-right)',              'Should be green (API Connected)'),
    ('Settings page → paste your API keys → Save',         'Preview shows first 6 chars of key'),
    ('Place Order → BUY BTCUSDT MARKET qty=0.001',         'Should show Order Placed card'),
    ('Order History',                                       'New order should appear with FILLED status'),
    ('Account → Open Positions',                           'BTCUSDT position should show with Mark/UPnL/ROE%'),
]
add_table(doc,
    ['Action', 'Expected Result'],
    checklist,
    col_widths=[3.2, 3.4]
)


# 9.8 Troubleshooting
add_heading(doc, '9.8  Common Issues & Fixes', 2)
add_table(doc,
    ['Symptom', 'Likely Cause', 'Fix'],
    [
        ['"API Offline" dot on dashboard',
         'Wrong API key or network',
         'Check Settings page — paste correct testnet keys; verify testnet.binancefuture.com is reachable'],
        ['Mark / UPnL / ROE% show "—" in Account',
         'No open positions',
         'Place a BUY order first — positions only appear when positionAmt ≠ 0'],
        ['Order status stuck at NEW',
         'Auto-sync not running',
         'Restart backend; check logs/trading_bot.log for errors'],
        ['Docker: port already in use',
         'Another service on 3000/8000/27017',
         'Stop conflicting service, or change ports in docker-compose.yml'],
        ['MongoDB connection refused (manual setup)',
         'MongoDB not running',
         'Start MongoDB service (see step 9.6 Step 1)'],
        ['"Quantity exceeds position size"',
         'Entered qty > open position',
         'Use the 100% button in the Exit modal to auto-fill max qty'],
    ],
    col_widths=[2.0, 1.8, 2.8]
)

add_divider(doc)


# ── 10. SECURITY NOTES ────────────────────────────────────────────────────────
add_heading(doc, '10. Security Notes', 1)
add_bullet(doc, 'The .env file contains your API keys and is excluded from git (.gitignore). Never commit it.')
add_bullet(doc, 'The Settings API endpoint returns only a masked preview of the key (first 6 + last 4 chars).')
add_bullet(doc, 'This application is designed for the Testnet only. Do not use production Binance keys.')
add_bullet(doc, 'reduceOnly=true is enforced on all exit orders, preventing accidental position reversal.')
add_bullet(doc, 'CORS is restricted to localhost:3000 and localhost:5173 by default.')

add_divider(doc)


# ── FOOTER ────────────────────────────────────────────────────────────────────
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('FuturesBot v1.0  ·  Binance USDT-M Futures Testnet  ·  FastAPI + React + MongoDB')
r.font.size = Pt(8.5)
r.font.color.rgb = C_LGRAY
r.font.italic = True


# ── SAVE ─────────────────────────────────────────────────────────────────────
output_path = r'C:\Users\rajka\OneDrive\Desktop\ALGO\ALGO_GitHub\ALGO_Files\TRADINGBOTBINANCE\FuturesBot_Architecture_Guide.docx'
doc.save(output_path)
print(f'Document saved: {output_path}')
