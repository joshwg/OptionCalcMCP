# Option Calculator - MCP Server Edition

A comprehensive Black-Scholes option calculator with MCP (Model Context Protocol) server architecture. The business logic runs on an MCP server that can be deployed to Railway, while the client can be a desktop app (Tkinter), mobile app (Kivy), or any MCP-compatible client.

## 🎯 Features

### Core Functionality
- **Multiple Pricing Models**
  - Black-Scholes for European options
  - Binomial Tree for American options
  
- **Complete Greeks Calculation**
  - Delta, Gamma, Theta, Vega, Rho
  
- **Real-time Market Data**
  - Yahoo Finance integration
  - Live stock prices and option chains
  - Historical volatility calculation
  
- **Advanced Features**
  - Ticker search with autocomplete
  - Multiple calculator windows
  - Dividend yield adjustments
  - Earnings date tracking

## 🏗️ Architecture

### MCP Server (mcp-server/)
The business logic server providing tools via MCP protocol:
- Option pricing calculations
- Greeks calculations
- Stock data fetching
- Historical volatility
- Ticker search
- Option chain retrieval

**Deploy to:** Railway, AWS, Azure, or run locally

### Desktop Client
Tkinter-based GUI that connects to the MCP server:
- User-friendly interface
- Multiple windows support
- Real-time data updates
- Configurable for local or remote server

### Mobile Client (kivy_app/)
Kivy-based mobile application (can also connect to MCP server)

## 🚀 Quick Start

### Option 1: Use Existing MCP Server (Recommended)

If you already have the MCP server deployed on Railway:

1. **Install Client Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Server URL**
   Create a `.env` file:
   ```env
   MCP_SERVER_MODE=remote
   MCP_SERVER_URL=https://your-app.railway.app
   ```

3. **Run Calculator**
   ```bash
   python main.py
   ```

### Option 2: Deploy Your Own MCP Server

1. **Deploy to Railway**
   ```bash
   cd mcp-server
   
   # Option A: Via Railway CLI
   npm i -g @railway/cli
   railway login
   railway init
   railway up
   
   # Option B: Via GitHub
   # Push to GitHub, then connect to Railway
   ```

2. **Or Run Server Locally**
   ```bash
   cd mcp-server
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python server.py
   ```

3. **Configure Client**
   ```env
   # For local server
   MCP_SERVER_MODE=local
   MCP_SERVER_COMMAND=python mcp-server/server.py
   ```

## 📁 Project Structure

```
OptionCalculator/
├── mcp-server/              # MCP Server (deploy to Railway)
│   ├── server.py           # Main server with all tools
│   ├── requirements.txt    # Server dependencies
│   ├── Procfile           # Railway deployment config
│   ├── railway.json       # Railway settings
│   └── README.md          # Server documentation
│
├── main.py                 # Desktop app entry point
├── calculator_window.py    # Main calculator UI
├── calculator_operations.py # Calculator logic (MCP client)
├── mcp_client.py          # MCP client wrapper
├── config_manager.py       # Configuration management
│
├── utils/                  # Utility modules
│   ├── font_manager.py
│   ├── input_validator.py
│   ├── suggestion_widget.py
│   └── threading_helper.py
│
├── kivy_app/              # Mobile application
│   ├── main.py
│   ├── optioncalculator.kv
│   └── screens/
│
├── MIGRATION_GUIDE.md      # How to migrate to MCP
├── deploy_mcp.bat         # Windows deployment script
└── deploy_mcp.sh          # Linux/Mac deployment script
```

## 🛠️ Development

### Requirements
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation
```bash
# Clone repository
git clone <your-repo-url>
cd OptionCalculator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r mcp-server/requirements.txt
```

### Running Locally
```bash
# Terminal 1: Start MCP server
cd mcp-server
python server.py

# Terminal 2: Run calculator
python main.py
```

### Testing
```bash
# Test MCP server tools
python mcp_client.py

# Run unit tests
python test_option_pricing.py
python test_yahoo_data.py
python test_dividend_normalization.py
```

## 🎮 Usage

### Basic Workflow
1. **Load Stock Data**
   - Enter ticker symbol (e.g., AAPL, MSFT)
   - Click "Load Stock Data"
   - Current price and dividend yield auto-populate

2. **Calculate Option Price**
   - Enter strike price
   - Select expiration date
   - Adjust volatility if needed
   - Choose pricing model
   - Click "Calculate Price"

3. **View Results**
   - Call and Put prices
   - All Greeks (Delta, Gamma, Theta, Vega, Rho)
   - Intrinsic and time value

### Advanced Features

**Multiple Windows**: Press `Ctrl+1` through `Ctrl+9` to open additional calculator windows for different stocks.

**Historical Volatility**: Click "Get Historical Volatility" to calculate from past prices.

**Option Chain**: View real market option prices and implied volatilities.

**Ticker Search**: Start typing a company name for autocomplete suggestions.

## 🔧 Configuration

### Environment Variables
Create a `.env` file:

```env
# Server Mode
MCP_SERVER_MODE=local|remote

# Local Server
MCP_SERVER_COMMAND=python mcp-server/server.py

# Remote Server (Railway)
MCP_SERVER_URL=https://your-app.railway.app

# UI Settings
DEFAULT_RISK_FREE_RATE=0.05
DEFAULT_VOLATILITY=0.30
```

### Config File
Edit `config.json` for persistent settings:

```json
{
  "theme": "light",
  "default_risk_free_rate": 0.05,
  "default_volatility": 0.30,
  "mcp_server_url": "https://your-app.railway.app"
}
```

## 🚢 Deployment

### Deploy MCP Server to Railway

**Method 1: Railway CLI**
```bash
cd mcp-server
railway login
railway init
railway up
```

**Method 2: GitHub Integration**
1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Select repository
5. Railway auto-deploys

**Method 3: Quick Deploy Button**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

### Desktop App Distribution
```bash
# Create standalone executable with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## 📚 MCP Tools Reference

The server provides these tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_stock_info` | Get stock data | ticker |
| `calculate_option_price` | Price options | S, K, T, r, σ, type, model |
| `calculate_greeks` | Calculate Greeks | S, K, T, r, σ, type |
| `get_historical_volatility` | Historical vol | ticker, days |
| `search_tickers` | Search stocks | query, max_results |
| `get_option_chain` | Get option chain | ticker, expiration |

See [mcp-server/README.md](mcp-server/README.md) for detailed API documentation.

## 📖 Documentation

- [Migration Guide](MIGRATION_GUIDE.md) - Converting to MCP architecture
- [MCP Server README](mcp-server/README.md) - Server documentation
- [Test README](TEST_README.md) - Testing information

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🐛 Known Issues

- Yahoo Finance API rate limiting may occur with frequent requests
- Some tickers may have limited option chain data
- Historical volatility requires sufficient price history

## 💡 Tips

- Use historical volatility as starting point for implied volatility
- Compare Black-Scholes vs Binomial for American options
- Check dividend yield impact on option prices
- Monitor Greeks for risk management
- Save multiple windows for portfolio analysis

## 🔗 Links

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Railway Documentation](https://docs.railway.app)
- [Yahoo Finance](https://finance.yahoo.com)
- [Black-Scholes Model](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model)

## ⚠️ Disclaimer

This tool is for educational and informational purposes only. Not financial advice. Use at your own risk.

---

**Built with**: Python, MCP, Railway, NumPy, SciPy, Tkinter, yfinance
