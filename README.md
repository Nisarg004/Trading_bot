# Trading Bot — Binance Futures Testnet

A Python CLI application that places orders on the Binance USDT-M Futures Testnet.
Supports Market, Limit, and Stop-Limit orders with rich terminal output, structured
logging, and an interactive guided mode.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # BinanceClient — Futures Testnet API wrapper
│   ├── orders.py          # OrderManager — place_market/limit/stop_limit_order
│   ├── validators.py      # InputValidator — validates all CLI inputs
│   └── logging_config.py  # Structured file + console logging
├── cli.py                 # Click CLI entry point (order / interactive / status)
├── test_connection.py     # Quick connectivity check for Testnet API
├── logs/
│   └── trading_bot.log    # Rotating log file (auto-created on first run)
├── .env.example           # Environment variable template
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Nisarg004/Trading_bot
cd trading_bot
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API credentials

Copy the example env file and fill in your Binance Futures Testnet keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

To get testnet credentials:

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Go to **API Key** → generate a key pair

---

## How to Run

### Place a Market order

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a Limit order

```bash
python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3200.00
```

### Place a Stop-Limit order

```bash
python cli.py order --symbol BTCUSDT --side BUY --type STOP_LIMIT \
  --quantity 0.01 --price 75500 --stop-price 75000
```

### Interactive guided mode

Step-by-step prompts with inline validation and order confirmation:

```bash
python cli.py interactive
```

Example session:

```
Binance Futures — Interactive Order Entry

Symbol (e.g. BTCUSDT): BTCUSDT
Side [BUY/SELL]: BUY
Order type [MARKET/LIMIT/STOP_LIMIT]: LIMIT
Limit price: 44000
Quantity: 0.01

          Order Request Summary
┌──────────────┬──────────────────┐
│ Symbol       │ BTCUSDT          │
│ Side         │ BUY              │
│ Type         │ LIMIT            │
│ Quantity     │ 0.01             │
│ Price        │ 44000.00000000   │
└──────────────┴──────────────────┘
Confirm order? [y/N]: y
✓ Order placed successfully
```

### Account status

Prints Available Balance, Total Wallet Balance, and Total Unrealized PnL:

```bash
python cli.py status
```

---

## Assumptions

- **Testnet only.** All API calls target `https://testnet.binancefuture.com`. No real funds are used.
- **USDT-M Futures.** Only USDT-margined perpetual contracts are supported (symbols ending in `USDT` or `BUSD`).
- **Stop-Limit testnet limitation.** The Binance Futures Testnet currently returns `-4120` for `STOP` order types on the standard `/fapi/v1/order` endpoint, despite listing it in `exchangeInfo`. The code is correct and the order reaches the API; this is a known testnet regression. The production Futures API supports it normally.
- **Quantities and prices** are passed as strings to avoid floating-point precision issues when sent to Binance.
- **Time-in-force** for Limit and Stop-Limit orders defaults to `GTC` (Good Till Cancelled).

---

## Logging

All API activity is written to `logs/trading_bot.log`. The log rotates at 5 MB
(up to 3 backups). Console output is `INFO` and above; the file captures `DEBUG`
and above, including full request params and raw API responses.

Sample log entries:

```
2026-04-15 03:21:14 | INFO  | bot.client | Placed MARKET BUY 0.0100 BTCUSDT → orderId: 13035625648 | status: NEW
2026-04-15 03:40:10 | INFO  | bot.client | Placed LIMIT SELL 0.0100 BTCUSDT → orderId: 13035640403 | status: NEW
```
