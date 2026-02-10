# Option Calculator MCP Server

A Model Context Protocol (MCP) server that provides option pricing, Greeks calculation, and stock market data tools. Deploy this server on Railway to access powerful financial calculations from any MCP client.

## Features

### Tools Provided

1. **get_stock_info** - Get comprehensive stock information
   - Current price, volume, dividend yield
   - Company name and earnings date
   - Previous close data

2. **calculate_option_price** - Price options using industry-standard models
   - Black-Scholes model for European options
   - Binomial Tree model for American options
   - Support for both calls and puts

3. **calculate_greeks** - Calculate option Greeks
   - Delta (price sensitivity)
   - Gamma (delta sensitivity)
   - Theta (time decay)
   - Vega (volatility sensitivity)
   - Rho (interest rate sensitivity)

4. **get_historical_volatility** - Calculate historical volatility
   - Configurable lookback period
   - Annualized volatility calculation

5. **search_tickers** - Search for stock tickers
   - Search by company name or symbol
   - Returns ticker, company name, and exchange

6. **get_option_chain** - Get real option chain data
   - Call and put options
   - Strike prices, bid/ask, volume
   - Implied volatility data

## Deployment on Railway

### Prerequisites
- Railway account ([railway.app](https://railway.app))
- Git repository

### Steps

1. **Initialize Git Repository** (if not already done)
   ```bash
   cd mcp-server
   git init
   git add .
   git commit -m "Initial MCP server setup"
   ```

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect the configuration

3. **Configure Environment** (if needed)
   - Railway automatically installs dependencies from `requirements.txt`
   - The `Procfile` specifies how to run the server
   - No additional environment variables required

4. **Get Your Server URL**
   - After deployment, Railway provides a public URL
   - Use this URL to connect your MCP clients

### Alternative: Deploy from CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize and deploy
railway init
railway up
```

## Local Development

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Run the MCP server
python server.py
```

The server communicates via stdio (standard input/output) following the MCP protocol.

### Testing Tools

You can test the server using the MCP Inspector or any MCP client:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run inspector
mcp-inspector python server.py
```

## Usage Examples

### Get Stock Information
```json
{
  "tool": "get_stock_info",
  "arguments": {
    "ticker": "AAPL"
  }
}
```

### Calculate Option Price
```json
{
  "tool": "calculate_option_price",
  "arguments": {
    "stock_price": 150.0,
    "strike_price": 155.0,
    "time_to_expiration": 0.25,
    "risk_free_rate": 0.05,
    "volatility": 0.30,
    "option_type": "call",
    "model": "black-scholes"
  }
}
```

### Calculate Greeks
```json
{
  "tool": "calculate_greeks",
  "arguments": {
    "stock_price": 150.0,
    "strike_price": 155.0,
    "time_to_expiration": 0.25,
    "risk_free_rate": 0.05,
    "volatility": 0.30,
    "option_type": "call"
  }
}
```

### Search Tickers
```json
{
  "tool": "search_tickers",
  "arguments": {
    "query": "apple",
    "max_results": 5
  }
}
```

## Architecture

The server is built using:
- **MCP SDK** - Model Context Protocol implementation
- **yfinance** - Real-time stock market data
- **NumPy & SciPy** - Mathematical computations
- **Black-Scholes Model** - European option pricing
- **Binomial Tree Model** - American option pricing

## Configuration

### Procfile
Specifies how Railway should run the server:
```
web: python -m mcp.server.stdio server:server
```

### railway.json
Railway deployment configuration:
- Uses Nixpacks builder
- Single replica deployment
- Automatic restart on failure

## API Reference

All tools follow the MCP protocol and return JSON responses.

### Error Handling
All tools return standardized error responses:
```json
{
  "success": false,
  "error": "Error description"
}
```

### Success Responses
Success responses vary by tool but always include relevant data in JSON format.

## Limitations

- Real-time data requires active internet connection
- Yahoo Finance API rate limits may apply
- Historical volatility calculations require sufficient data history
- Option chain data availability depends on ticker and exchange

## Support

For issues or questions:
- Create an issue in the repository
- Check MCP documentation at [modelcontextprotocol.io](https://modelcontextprotocol.io)
- Review Railway documentation at [docs.railway.app](https://docs.railway.app)

## License

MIT License - See LICENSE file for details
