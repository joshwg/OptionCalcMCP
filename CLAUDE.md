# OptionCalculator

Black-Scholes/Binomial Tree option pricing tool with MCP server architecture. Business logic runs as an MCP server (deployable to Railway); clients connect via HTTP/SSE transport.

## Architecture

```
mcp-server/server.py      # MCP server — all pricing logic, Greeks, market data
main.py                   # Desktop app entry point (Tkinter)
calculator_window.py      # Tkinter UI
calculator_operations.py  # MCP client wrapper for desktop app
mcp_client.py             # Low-level MCP client
config_manager.py         # .env / config.json loading
utils/                    # Font, input validation, threading, autocomplete widgets
kivy_app/                 # Android/mobile app (Kivy + KivyMD)
  screens/calculator_screen.py  # Main mobile screen (currently modified)
```

## Running Locally

```bash
# Terminal 1: MCP server
cd mcp-server
python server.py          # listens on PORT env var (default 8080)

# Terminal 2: desktop client
python main.py
```

## Configuration

`.env` file at project root:
```env
MCP_SERVER_MODE=local|remote
MCP_SERVER_COMMAND=python mcp-server/server.py   # local mode
MCP_SERVER_URL=https://{project-url}.up.railway.app  # remote mode
DEFAULT_RISK_FREE_RATE=0.05
DEFAULT_VOLATILITY=0.30
```

`config.json` stores persistent UI settings (theme, defaults, server URL).

## Dependencies

- Desktop client: `requirements.txt` (numpy, scipy, yfinance, pandas, requests, pytz)
- MCP server: `mcp-server/requirements.txt`
- Mobile: `kivy_app/requirements-kivy.txt`
- Single supported environment: `venv` (Linux/Python 3.12 in WSL2)

## Tests

```bash
python test_option_pricing.py
python test_yahoo_data.py
python test_dividend_normalization.py
python test_mcp_server.py
python test_ticker_search.py
```

## MCP Server Tools

| Tool | Key params |
|------|-----------|
| `get_stock_info` | ticker |
| `calculate_option_price` | S, K, T, r, σ, type, model (black-scholes\|binomial) |
| `calculate_greeks` | S, K, T, r, σ, type |
| `get_historical_volatility` | ticker, days |
| `search_tickers` | query, max_results |
| `get_option_chain` | ticker, expiration_date |

## Environment

All shell commands run in **WSL2 (Ubuntu)**, not PowerShell. Use `bash` via the Bash tool.

## Deployment

MCP server deploys to Railway via `mcp-server/Procfile` and `railway.json`. The server uses HTTP/SSE transport (`/sse` and `/messages/` endpoints). Health check at `/health`.

```bash
cd mcp-server
railway login && railway up
```

## Key Notes

- Dividend yield and implied volatility from Yahoo Finance may arrive as percentages (>0.5 or >2) — `normalize_dividend_yield()` and `normalize_implied_volatility()` handle this.
- Black-Scholes is for European options; Binomial Tree (`binomial_tree_american`) handles early exercise for American options.
- `Ctrl+1` through `Ctrl+9` opens multiple calculator windows in the desktop app.
