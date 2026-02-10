# Quick Reference Guide

## 🚀 5-Minute Quick Start

### 1. Local Testing
```bash
# Install dependencies
pip install mcp>=0.9.0

# Test the MCP server
python test_mcp_server.py
```

### 2. Deploy to Railway
```bash
cd mcp-server
railway login
railway init
railway up
```

### 3. Use in Your App
```python
from mcp_client import MCPClient

client = MCPClient("https://your-app.railway.app")
result = client.get_stock_info("AAPL")
```

---

## 📖 Common Commands

### Development
```bash
# Run MCP server locally
cd mcp-server
python server.py

# Run test suite
python test_mcp_server.py

# Run example code
python example_mcp_usage.py

# Run calculator
python main.py
```

### Deployment
```bash
# Deploy to Railway (CLI)
cd mcp-server
railway up

# Check Railway logs
railway logs

# Open Railway dashboard
railway open

# Deploy from GitHub
# Just push to GitHub and connect via Railway dashboard
```

### Testing
```bash
# Test all MCP tools
python test_mcp_server.py

# Test specific functionality
python test_option_pricing.py
python test_yahoo_data.py
```

---

## 🛠️ MCP Tools Quick Reference

### 1. get_stock_info
```python
result = client.get_stock_info("AAPL")
# Returns: price, company name, volume, dividend yield
```

### 2. calculate_option_price
```python
result = client.calculate_option_price(
    stock_price=150.0,
    strike_price=155.0,
    time_to_expiration=0.25,
    risk_free_rate=0.05,
    volatility=0.30,
    option_type="call",
    model="black-scholes"
)
# Returns: option price
```

### 3. calculate_greeks
```python
greeks = client.calculate_greeks(
    stock_price=150.0,
    strike_price=155.0,
    time_to_expiration=0.25,
    risk_free_rate=0.05,
    volatility=0.30,
    option_type="call"
)
# Returns: delta, gamma, theta, vega, rho
```

### 4. get_historical_volatility
```python
result = client.get_historical_volatility("AAPL", days=30)
# Returns: annualized volatility
```

### 5. search_tickers
```python
results = client.search_tickers("apple", max_results=10)
# Returns: list of matching tickers
```

### 6. get_option_chain
```python
chain = client.get_option_chain("AAPL", "2024-12-20")
# Returns: calls and puts with strikes, prices, IV
```

---

## 🔧 Configuration

### .env File
```env
MCP_SERVER_MODE=remote
MCP_SERVER_URL=https://your-app.railway.app
```

### Python Code
```python
import os
from mcp_client import MCPClient

mode = os.getenv("MCP_SERVER_MODE", "local")
url = os.getenv("MCP_SERVER_URL", "python mcp-server/server.py")
client = MCPClient(url)
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `mcp-server/server.py` | Main MCP server |
| `mcp_client.py` | Client library |
| `test_mcp_server.py` | Test suite |
| `example_mcp_usage.py` | Usage examples |
| `.env` | Configuration |
| `RAILWAY_QUICKSTART.md` | Deployment guide |
| `MIGRATION_GUIDE.md` | Migration steps |

---

## 🐛 Troubleshooting

### Server won't start
```bash
cd mcp-server
pip install -r requirements.txt
python server.py
```

### Tests fail
- Check internet connection (Yahoo Finance requires it)
- Verify server is running
- Check dependencies installed

### Client can't connect
```python
# Test locally first
client = MCPClient("python mcp-server/server.py")

# Then test Railway
client = MCPClient("https://your-app.railway.app")
```

### Railway deployment fails
- Check `Procfile` exists
- Verify `requirements.txt` is complete
- Check Railway logs: `railway logs`

---

## 💡 Tips & Tricks

### Development
- Use local mode during development
- Test with `test_mcp_server.py` before deploying
- Keep Railway URL in `.env` file

### Production
- Use Railway URL for production
- Monitor Railway logs for errors
- Set up Railway alerts

### Performance
- Cache stock data in your app
- Use appropriate timeout values
- Handle network errors gracefully

---

## 🔗 Quick Links

- **MCP Documentation**: https://modelcontextprotocol.io
- **Railway Dashboard**: https://railway.app/dashboard
- **Railway Docs**: https://docs.railway.app
- **yfinance Docs**: https://pypi.org/project/yfinance/

---

## 📞 Getting Help

1. **Check Documentation**
   - [RAILWAY_QUICKSTART.md](RAILWAY_QUICKSTART.md)
   - [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
   - [mcp-server/README.md](mcp-server/README.md)

2. **Run Tests**
   ```bash
   python test_mcp_server.py
   ```

3. **Check Logs**
   ```bash
   railway logs
   ```

4. **Create Issue**
   - Include error message
   - Describe what you tried
   - Show relevant code

---

## ✅ Checklist

### Before Deploying
- [ ] Tested locally
- [ ] All tests pass
- [ ] Dependencies listed in requirements.txt
- [ ] Procfile configured
- [ ] Git repository initialized

### After Deploying
- [ ] Railway deployment successful
- [ ] Got server URL
- [ ] Updated .env with URL
- [ ] Tested client connection
- [ ] Calculator app works

### For Production
- [ ] Error handling in place
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Backup plan ready
- [ ] Documentation complete

---

## 🎯 Next Steps

1. ✅ Deploy MCP server to Railway
2. ✅ Update calculator to use MCP client
3. ⬜ Add more features to server
4. ⬜ Build web interface
5. ⬜ Add caching layer
6. ⬜ Implement rate limiting
7. ⬜ Add authentication (if needed)

---

**Need more detail? Check the full documentation files!**
