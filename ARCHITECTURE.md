# Option Calculator MCP Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    CLIENT APPLICATIONS                          │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Desktop App   │  │   Mobile App   │  │   Web App      │  │
│  │   (Tkinter)    │  │    (Kivy)      │  │  (React/Vue)   │  │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  │
│          │                   │                    │            │
│          └───────────────────┼────────────────────┘            │
│                              │                                 │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                               │ MCP Protocol
                               │ (JSON-RPC)
                               │
┌──────────────────────────────▼─────────────────────────────────┐
│                                                                 │
│                   MCP CLIENT LIBRARY                            │
│                   (mcp_client.py)                               │
│                                                                 │
│  • Protocol handling (stdio/HTTP)                               │
│  • Request/response serialization                               │
│  • Error handling and retries                                   │
│  • Connection management                                        │
│                                                                 │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               │ Network (HTTPS)
                               │ or Local (stdio)
                               │
┌──────────────────────────────▼─────────────────────────────────┐
│                                                                 │
│                    RAILWAY CLOUD PLATFORM                       │
│                   (or Local Development)                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │              MCP SERVER (server.py)                     │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │              TOOL: get_stock_info               │  │  │
│  │  │  • Fetches current price                        │  │  │
│  │  │  • Gets company info                            │  │  │
│  │  │  • Returns dividend yield                       │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         TOOL: calculate_option_price            │  │  │
│  │  │  • Black-Scholes model                          │  │  │
│  │  │  • Binomial tree model                          │  │  │
│  │  │  • Call and Put pricing                         │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │           TOOL: calculate_greeks                │  │  │
│  │  │  • Delta (price sensitivity)                    │  │  │
│  │  │  • Gamma (delta sensitivity)                    │  │  │
│  │  │  • Theta (time decay)                           │  │  │
│  │  │  • Vega (volatility sensitivity)                │  │  │
│  │  │  • Rho (interest rate sensitivity)              │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │      TOOL: get_historical_volatility            │  │  │
│  │  │  • Downloads price history                      │  │  │
│  │  │  • Calculates log returns                       │  │  │
│  │  │  • Annualizes volatility                        │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │            TOOL: search_tickers                 │  │  │
│  │  │  • Yahoo Finance API search                     │  │  │
│  │  │  • Returns symbol, name, exchange               │  │  │
│  │  │  • Filters by equity/ETF                        │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │           TOOL: get_option_chain                │  │  │
│  │  │  • Live option chain data                       │  │  │
│  │  │  • Strike prices, bid/ask                       │  │  │
│  │  │  • Implied volatility                           │  │  │
│  │  │  • Volume and open interest                     │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ External APIs
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                                                                  │
│                   EXTERNAL DATA SOURCES                          │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Yahoo Finance   │  │  Market Data     │  │  Historical  │ │
│  │      API         │  │    Providers     │  │    Prices    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Calculating Option Price

```
1. User enters parameters in Desktop App
   ↓
2. Desktop App calls: mcp_client.calculate_option_price(...)
   ↓
3. MCP Client formats JSON-RPC request:
   {
     "method": "tools/call",
     "params": {
       "name": "calculate_option_price",
       "arguments": {
         "stock_price": 150.0,
         "strike_price": 155.0,
         ...
       }
     }
   }
   ↓
4. Request sent to Railway server via HTTPS
   ↓
5. MCP Server receives and validates request
   ↓
6. Server executes Black-Scholes calculation:
   - Calculates d1 and d2
   - Applies normal distribution
   - Computes option price
   ↓
7. Server returns JSON response:
   {
     "result": {
       "price": 8.45,
       "model": "black-scholes",
       "option_type": "call"
     }
   }
   ↓
8. MCP Client parses response
   ↓
9. Desktop App displays: "Call Price: $8.45"
```

## Deployment Flow

```
┌──────────────────┐
│  Developer PC    │
│                  │
│  1. Write code   │
│  2. Test locally │
│  3. Commit to    │
│     GitHub       │
└────────┬─────────┘
         │
         │ git push
         │
         ▼
┌────────────────────┐
│      GitHub        │
│   (Repository)     │
└────────┬───────────┘
         │
         │ Webhook/CLI
         │
         ▼
┌────────────────────────────┐
│        Railway             │
│                            │
│  1. Detect changes         │
│  2. Install dependencies   │
│  3. Build container        │
│  4. Deploy server          │
│  5. Assign public URL      │
│                            │
│  https://your-app.        │
│        railway.app         │
└────────────────────────────┘
```

## Local vs Production Deployment

### Local Development
```
┌──────────────┐         ┌──────────────┐
│              │  stdio  │              │
│  Calculator  │◄───────►│  MCP Server  │
│   (Client)   │         │   (Local)    │
│              │         │              │
└──────────────┘         └──────────────┘
     Same Machine
```

### Production Deployment
```
┌──────────────┐         ┌──────────────┐
│              │  HTTPS  │              │
│  Calculator  │◄───────►│  MCP Server  │
│   (Client)   │         │  (Railway)   │
│              │         │              │
└──────────────┘         └──────────────┘
  User's Machine         Cloud Platform
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│           CLIENT SIDE                   │
├─────────────────────────────────────────┤
│  • Python 3.8+                          │
│  • Tkinter (Desktop UI)                 │
│  • Kivy (Mobile UI)                     │
│  • MCP Client Library                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           SERVER SIDE                   │
├─────────────────────────────────────────┤
│  • Python 3.8+                          │
│  • MCP SDK (Model Context Protocol)    │
│  • NumPy (Mathematical operations)      │
│  • SciPy (Statistical functions)        │
│  • yfinance (Market data)               │
│  • pandas (Data manipulation)           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          INFRASTRUCTURE                 │
├─────────────────────────────────────────┤
│  • Railway (Cloud hosting)              │
│  • GitHub (Version control)             │
│  • Nixpacks (Build system)              │
└─────────────────────────────────────────┘
```

## Security & Scalability

```
┌────────────────────────────────────────────┐
│              Security Layer                │
├────────────────────────────────────────────┤
│  • HTTPS encryption                        │
│  • Input validation                        │
│  • Rate limiting (Railway built-in)       │
│  • Error handling                          │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│           Scalability Features             │
├────────────────────────────────────────────┤
│  • Stateless server design                 │
│  • Horizontal scaling ready                │
│  • Caching potential (future)              │
│  • Multiple client support                 │
└────────────────────────────────────────────┘
```

## Benefits Visualization

```
                 BEFORE (Monolithic)
┌──────────────────────────────────────────────┐
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │         Desktop App                 │   │
│  │                                     │   │
│  │  • UI Code                          │   │
│  │  • Business Logic                   │   │
│  │  • Data Fetching                    │   │
│  │  • Calculations                     │   │
│  │  • All tightly coupled              │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ❌ Hard to test                             │
│  ❌ Can't reuse logic                        │
│  ❌ Must update all clients                  │
│                                              │
└──────────────────────────────────────────────┘


                 AFTER (MCP Architecture)
┌──────────────────────────────────────────────┐
│              Clients                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Desktop  │  │  Mobile  │  │   Web    │  │
│  │   App    │  │   App    │  │   App    │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  │
│        └─────────────┼─────────────┘        │
│                      │                       │
│        ┌─────────────▼─────────────┐        │
│        │      MCP Protocol         │        │
│        └─────────────┬─────────────┘        │
│                      │                       │
│        ┌─────────────▼─────────────┐        │
│        │      Business Logic       │        │
│        │      (MCP Server)         │        │
│        │      on Railway           │        │
│        └───────────────────────────┘        │
│                                              │
│  ✅ Easy to test                             │
│  ✅ Reusable across platforms                │
│  ✅ Update once, benefits all               │
│  ✅ Scalable architecture                    │
│                                              │
└──────────────────────────────────────────────┘
```
