# Migration Guide: Converting to MCP Server Architecture

## Overview

This guide explains how to migrate the Option Calculator from a standalone desktop application to an MCP (Model Context Protocol) server architecture deployed on Railway.

## What Changed?

### Before (Monolithic Desktop App)
- All logic in local Python modules
- Direct function calls
- Tkinter GUI tightly coupled with business logic
- Limited scalability

### After (MCP Server + Client)
- Business logic in MCP server (can be deployed anywhere)
- Client communicates via MCP protocol
- Clear separation of concerns
- Highly scalable and reusable

## Architecture

```
┌─────────────────────────────────────┐
│   Desktop Client (Tkinter/Kivy)    │
│                                     │
│  ┌───────────────────────────────┐ │
│  │      MCP Client Library       │ │
│  └───────────────────────────────┘ │
└──────────────┬──────────────────────┘
               │ MCP Protocol
               │ (JSON-RPC over stdio/HTTP)
               │
┌──────────────▼──────────────────────┐
│     Railway (Cloud Platform)        │
│                                     │
│  ┌───────────────────────────────┐ │
│  │    MCP Server (server.py)     │ │
│  │                               │ │
│  │  Tools:                       │ │
│  │  - get_stock_info            │ │
│  │  - calculate_option_price    │ │
│  │  - calculate_greeks          │ │
│  │  - get_historical_volatility │ │
│  │  - search_tickers            │ │
│  │  - get_option_chain          │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Step-by-Step Migration

### Step 1: Deploy MCP Server to Railway

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Push MCP Server to Git**
   ```bash
   cd mcp-server
   git init
   git add .
   git commit -m "Initial MCP server"
   git push origin main
   ```

3. **Deploy on Railway**
   - New Project → Deploy from GitHub
   - Select your repository
   - Select the `mcp-server` directory
   - Railway will auto-detect and deploy

4. **Get Server URL**
   - Once deployed, Railway provides a URL
   - Save this for client configuration

### Step 2: Update Client Code

Replace direct function calls with MCP client calls:

**Before:**
```python
import option_pricing as bs
import yahoo_data as yd

# Direct function call
price = bs.black_scholes_call(S, K, T, r, sigma)
info = yd.get_stock_info(ticker)
```

**After:**
```python
from mcp_client import MCPClient

# Initialize client (local or remote)
client = MCPClient("https://your-railway-url.railway.app")

# Call via MCP
result = client.calculate_option_price(
    stock_price=S,
    strike_price=K,
    time_to_expiration=T,
    risk_free_rate=r,
    volatility=sigma,
    option_type="call"
)
price = result["price"]

info = client.get_stock_info(ticker)
```

### Step 3: Update calculator_operations.py

Here's how to convert the main operations:

**Stock Data Loading:**
```python
# OLD
def load_stock_data(self):
    info = yd.get_stock_info(ticker)
    
# NEW
def load_stock_data(self):
    info = self.mcp_client.get_stock_info(ticker)
```

**Option Pricing:**
```python
# OLD
if model == "Black-Scholes":
    call_price = bs.black_scholes_call(S, K, T, r, sigma)
    put_price = bs.black_scholes_put(S, K, T, r, sigma)

# NEW
call_result = self.mcp_client.calculate_option_price(
    stock_price=S, strike_price=K, time_to_expiration=T,
    risk_free_rate=r, volatility=sigma, option_type="call",
    model="black-scholes"
)
call_price = call_result["price"]
```

**Greeks Calculation:**
```python
# OLD
greeks = bs.calculate_greeks(S, K, T, r, sigma, 'call')

# NEW
greeks = self.mcp_client.calculate_greeks(
    stock_price=S, strike_price=K, time_to_expiration=T,
    risk_free_rate=r, volatility=sigma, option_type="call"
)
```

### Step 4: Initialize MCP Client

Add to your calculator window initialization:

```python
from mcp_client import MCPClient

class OptionCalculatorWindow:
    def __init__(self):
        # Initialize MCP client
        # For local testing:
        self.mcp_client = MCPClient("python mcp-server/server.py")
        
        # For production (Railway):
        # self.mcp_client = MCPClient("https://your-app.railway.app")
        
        # Rest of initialization...
```

### Step 5: Update requirements.txt

Add MCP client dependency:
```
# Add to requirements.txt
mcp>=0.9.0
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Local development
MCP_SERVER_MODE=local
MCP_SERVER_COMMAND=python mcp-server/server.py

# Production
# MCP_SERVER_MODE=remote
# MCP_SERVER_URL=https://your-app.railway.app
```

Load in your app:
```python
import os
from dotenv import load_dotenv

load_dotenv()

server_mode = os.getenv("MCP_SERVER_MODE", "local")
if server_mode == "local":
    client = MCPClient(os.getenv("MCP_SERVER_COMMAND"))
else:
    client = MCPClient(os.getenv("MCP_SERVER_URL"))
```

## Testing

### Local Testing
```bash
# Terminal 1: Start MCP server
cd mcp-server
python server.py

# Terminal 2: Run client
python mcp_client.py
```

### Production Testing
```bash
# Update .env to use Railway URL
MCP_SERVER_MODE=remote
MCP_SERVER_URL=https://your-app.railway.app

# Run client
python main.py
```

## Benefits of This Architecture

1. **Scalability**: Server can handle multiple clients
2. **Separation**: Business logic separate from UI
3. **Reusability**: Server can be used by web apps, mobile apps, CLI tools
4. **Maintenance**: Update logic once on server, all clients benefit
5. **Testing**: Easier to test business logic independently
6. **Deployment**: Server can be deployed anywhere (Railway, AWS, Azure, etc.)

## Rollback Plan

If issues arise, you can easily switch back:

```python
# Use local modules instead of MCP
USE_MCP = False

if USE_MCP:
    from mcp_client import MCPClient
    client = MCPClient()
else:
    # Use old imports
    import option_pricing as bs
    import yahoo_data as yd
```

## Next Steps

1. ✅ Deploy MCP server to Railway
2. ✅ Update client code to use MCP client
3. ✅ Test locally with local MCP server
4. ✅ Test with Railway deployment
5. ✅ Update documentation
6. ✅ Deploy to production

## Support

- **MCP Documentation**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Issues**: Create an issue in the repository
