"""
Option Calculator MCP Server
Provides option pricing, Greeks calculation, and stock data tools via MCP
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from scipy.stats import norm
import yfinance as yf
import pytz
import requests

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
import uvicorn


# ==================== STOCK DATA FUNCTIONS ====================

def normalize_implied_volatility(iv_value):
    """Normalize implied volatility to decimal format (0.0 to 1.0 range)"""
    if iv_value is None or iv_value == 0:
        return 0
    if iv_value > 2:
        return iv_value / 100
    return iv_value


def normalize_dividend_yield(div_value):
    """Normalize dividend yield to decimal format (0.0 to 1.0 range)"""
    if div_value is None or div_value == 0:
        return 0
    if div_value > 0.5:
        return div_value / 100
    return div_value


def get_stock_info(ticker):
    """Get comprehensive stock information from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price:
            hist = stock.history(period='5d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        
        if not current_price:
            return {
                'success': False,
                'error': f'Could not fetch data for ticker: {ticker}'
            }
        
        company_name = info.get('longName') or info.get('shortName') or ticker
        previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        volume = info.get('volume') or info.get('regularMarketVolume')
        
        dividend_yield = info.get('dividendYield', 0) or 0
        dividend_yield = normalize_dividend_yield(dividend_yield)
        
        earnings_date = "unavailable"
        if 'earningsDate' in info and info['earningsDate']:
            try:
                if isinstance(info['earningsDate'], list) and len(info['earningsDate']) > 0:
                    earnings_timestamp = info['earningsDate'][0]
                else:
                    earnings_timestamp = info['earningsDate']
                
                if hasattr(earnings_timestamp, 'strftime'):
                    earnings_date = earnings_timestamp.strftime('%Y-%m-%d')
                else:
                    earnings_datetime = datetime.fromtimestamp(earnings_timestamp)
                    earnings_date = earnings_datetime.strftime('%Y-%m-%d')
            except:
                pass
        
        return {
            'success': True,
            'ticker': ticker,
            'company_name': company_name,
            'current_price': float(current_price),
            'previous_close': float(previous_close) if previous_close else None,
            'volume': int(volume) if volume else None,
            'dividend_yield': float(dividend_yield),
            'earnings_date': earnings_date
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_historical_volatility(ticker, days=30):
    """Calculate historical volatility from past stock prices"""
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)
        
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 2:
            return None
        
        returns = np.log(hist['Close'] / hist['Close'].shift(1))
        returns = returns.dropna()
        
        if len(returns) < 2:
            return None
        
        volatility = returns.std() * np.sqrt(252)
        return float(volatility)
    
    except Exception as e:
        return None


def search_tickers(query, max_results=10):
    """Search for stock tickers matching the query"""
    if not query or len(query) < 1:
        return []
    
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': max_results,
            'newsCount': 0,
            'enableFuzzyQuery': False,
            'quotesQueryId': 'tss_match_phrase_query'
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            
            results = []
            for quote in quotes[:max_results]:
                if quote.get('quoteType') in ['EQUITY', 'ETF']:
                    symbol = quote.get('symbol', '')
                    name = quote.get('longname') or quote.get('shortname', '')
                    exchange = quote.get('exchange', '')
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'exchange': exchange
                    })
            
            return results
        
        return []
    
    except Exception as e:
        return []


def get_option_chain(ticker, expiration_date=None):
    """Get option chain data for a specific ticker and expiration"""
    try:
        stock = yf.Ticker(ticker)
        
        if expiration_date is None:
            dates = stock.options
            if not dates:
                return {'success': False, 'error': 'No options available'}
            expiration_date = dates[0]
        
        opt_chain = stock.option_chain(expiration_date)
        
        calls_data = []
        for _, row in opt_chain.calls.iterrows():
            calls_data.append({
                'strike': float(row['strike']),
                'lastPrice': float(row['lastPrice']) if 'lastPrice' in row else None,
                'bid': float(row['bid']) if 'bid' in row else None,
                'ask': float(row['ask']) if 'ask' in row else None,
                'volume': int(row['volume']) if 'volume' in row and row['volume'] else 0,
                'openInterest': int(row['openInterest']) if 'openInterest' in row else 0,
                'impliedVolatility': normalize_implied_volatility(row.get('impliedVolatility', 0))
            })
        
        puts_data = []
        for _, row in opt_chain.puts.iterrows():
            puts_data.append({
                'strike': float(row['strike']),
                'lastPrice': float(row['lastPrice']) if 'lastPrice' in row else None,
                'bid': float(row['bid']) if 'bid' in row else None,
                'ask': float(row['ask']) if 'ask' in row else None,
                'volume': int(row['volume']) if 'volume' in row and row['volume'] else 0,
                'openInterest': int(row['openInterest']) if 'openInterest' in row else 0,
                'impliedVolatility': normalize_implied_volatility(row.get('impliedVolatility', 0))
            })
        
        return {
            'success': True,
            'expiration_date': expiration_date,
            'calls': calls_data,
            'puts': puts_data
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ==================== OPTION PRICING FUNCTIONS ====================

def black_scholes_call(S, K, T, r, sigma):
    """Calculate Black-Scholes price for a European call option"""
    if T <= 0:
        return max(S - K, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return float(call_price)


def black_scholes_put(S, K, T, r, sigma):
    """Calculate Black-Scholes price for a European put option"""
    if T <= 0:
        return max(K - S, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return float(put_price)


def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """Calculate option Greeks"""
    if T <= 0:
        return {
            'delta': 1.0 if S > K else 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Delta
    if option_type == 'call':
        delta = norm.cdf(d1)
    else:
        delta = norm.cdf(d1) - 1
    
    # Gamma (same for call and put)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    # Theta
    if option_type == 'call':
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
    
    # Vega (same for call and put)
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100
    
    # Rho
    if option_type == 'call':
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    
    return {
        'delta': float(delta),
        'gamma': float(gamma),
        'theta': float(theta),
        'vega': float(vega),
        'rho': float(rho)
    }


def binomial_tree_american(S, K, T, r, sigma, option_type='call', steps=100):
    """Calculate American option price using binomial tree"""
    if T <= 0:
        if option_type == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)
    
    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    
    # Initialize asset prices at maturity
    asset_prices = np.zeros(steps + 1)
    for i in range(steps + 1):
        asset_prices[i] = S * (u ** (steps - i)) * (d ** i)
    
    # Initialize option values at maturity
    option_values = np.zeros(steps + 1)
    for i in range(steps + 1):
        if option_type == 'call':
            option_values[i] = max(asset_prices[i] - K, 0)
        else:
            option_values[i] = max(K - asset_prices[i], 0)
    
    # Step back through the tree
    for j in range(steps - 1, -1, -1):
        for i in range(j + 1):
            asset_price = S * (u ** (j - i)) * (d ** i)
            option_values[i] = np.exp(-r * dt) * (p * option_values[i] + (1 - p) * option_values[i + 1])
            
            # Check for early exercise
            if option_type == 'call':
                intrinsic_value = max(asset_price - K, 0)
            else:
                intrinsic_value = max(K - asset_price, 0)
            
            option_values[i] = max(option_values[i], intrinsic_value)
    
    return float(option_values[0])


# ==================== MCP SERVER ====================

server = Server("option-calculator-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_stock_info",
            description="Get comprehensive stock information including price, volume, dividend yield, and earnings date",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT, TSLA)"
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="calculate_option_price",
            description="Calculate option price using Black-Scholes or Binomial Tree model",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_price": {
                        "type": "number",
                        "description": "Current stock price"
                    },
                    "strike_price": {
                        "type": "number",
                        "description": "Option strike price"
                    },
                    "time_to_expiration": {
                        "type": "number",
                        "description": "Time to expiration in years"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Risk-free interest rate (as decimal, e.g., 0.05 for 5%)"
                    },
                    "volatility": {
                        "type": "number",
                        "description": "Volatility (as decimal, e.g., 0.25 for 25%)"
                    },
                    "option_type": {
                        "type": "string",
                        "enum": ["call", "put"],
                        "description": "Type of option"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["black-scholes", "binomial"],
                        "description": "Pricing model to use (default: black-scholes)"
                    }
                },
                "required": ["stock_price", "strike_price", "time_to_expiration", "risk_free_rate", "volatility", "option_type"]
            }
        ),
        Tool(
            name="calculate_greeks",
            description="Calculate option Greeks (Delta, Gamma, Theta, Vega, Rho)",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_price": {
                        "type": "number",
                        "description": "Current stock price"
                    },
                    "strike_price": {
                        "type": "number",
                        "description": "Option strike price"
                    },
                    "time_to_expiration": {
                        "type": "number",
                        "description": "Time to expiration in years"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Risk-free interest rate (as decimal)"
                    },
                    "volatility": {
                        "type": "number",
                        "description": "Volatility (as decimal)"
                    },
                    "option_type": {
                        "type": "string",
                        "enum": ["call", "put"],
                        "description": "Type of option"
                    }
                },
                "required": ["stock_price", "strike_price", "time_to_expiration", "risk_free_rate", "volatility", "option_type"]
            }
        ),
        Tool(
            name="get_historical_volatility",
            description="Calculate historical volatility from past stock prices",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days to look back (default: 30)"
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="search_tickers",
            description="Search for stock tickers by company name or symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (company name or ticker symbol)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results (default: 10)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_option_chain",
            description="Get option chain data for a specific ticker",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Expiration date (YYYY-MM-DD format, optional)"
                    }
                },
                "required": ["ticker"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    try:
        if name == "get_stock_info":
            ticker = arguments["ticker"]
            result = get_stock_info(ticker)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "calculate_option_price":
            S = float(arguments["stock_price"])
            K = float(arguments["strike_price"])
            T = float(arguments["time_to_expiration"])
            r = float(arguments["risk_free_rate"])
            sigma = float(arguments["volatility"])
            option_type = arguments["option_type"]
            model = arguments.get("model", "black-scholes")
            
            if model == "binomial":
                price = binomial_tree_american(S, K, T, r, sigma, option_type)
            else:
                if option_type == "call":
                    price = black_scholes_call(S, K, T, r, sigma)
                else:
                    price = black_scholes_put(S, K, T, r, sigma)
            
            result = {
                "price": price,
                "model": model,
                "option_type": option_type
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "calculate_greeks":
            S = float(arguments["stock_price"])
            K = float(arguments["strike_price"])
            T = float(arguments["time_to_expiration"])
            r = float(arguments["risk_free_rate"])
            sigma = float(arguments["volatility"])
            option_type = arguments["option_type"]
            
            greeks = calculate_greeks(S, K, T, r, sigma, option_type)
            return [TextContent(type="text", text=json.dumps(greeks, indent=2))]
        
        elif name == "get_historical_volatility":
            ticker = arguments["ticker"]
            days = arguments.get("days", 30)
            volatility = get_historical_volatility(ticker, int(days))
            
            result = {
                "ticker": ticker,
                "days": days,
                "volatility": volatility
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_tickers":
            query = arguments["query"]
            max_results = arguments.get("max_results", 10)
            results = search_tickers(query, int(max_results))
            
            return [TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "get_option_chain":
            ticker = arguments["ticker"]
            expiration_date = arguments.get("expiration_date")
            result = get_option_chain(ticker, expiration_date)
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name="option-calculator-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


async def handle_messages(request: Request):
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def handle_health(_request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=handle_health),
    ]
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
