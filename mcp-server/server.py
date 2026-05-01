"""
Option Calculator MCP Server
Provides option pricing, Greeks calculation, and stock data tools via MCP
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any

import math

import numpy as np
from scipy.stats import norm
import pytz
import requests

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
import uvicorn


# ==================== HELPERS ====================

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')
POLYGON_BASE = 'https://api.polygon.io'


class _TTLCache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if entry and time.time() < entry[1]:
            return entry[0]
        self._store.pop(key, None)
        return None

    def set(self, key, value, ttl):
        self._store[key] = (value, time.time() + ttl)


_cache = _TTLCache()


def _polygon_get(path, params=None):
    p = {**(params or {}), 'apiKey': POLYGON_API_KEY}
    resp = requests.get(f'{POLYGON_BASE}{path}', params=p, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _polygon_next(next_url):
    sep = '&' if '?' in next_url else '?'
    resp = requests.get(f'{next_url}{sep}apiKey={POLYGON_API_KEY}', timeout=10)
    resp.raise_for_status()
    return resp.json()


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
    cached = _cache.get(f'stock_info:{ticker}')
    if cached:
        return cached
    try:
        snap = _polygon_get(f'/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}')
        t = snap.get('ticker', {})

        current_price = (
            (t.get('lastTrade') or {}).get('p')
            or (t.get('day') or {}).get('c')
            or (t.get('prevDay') or {}).get('c')
        )
        if not current_price:
            return {'success': False, 'error': f'Could not fetch data for ticker: {ticker}'}

        prev_close = (t.get('prevDay') or {}).get('c')
        volume = (t.get('day') or {}).get('v')

        ref = _polygon_get(f'/v3/reference/tickers/{ticker}')
        company_name = (ref.get('results') or {}).get('name') or ticker

        div_yield = 0.0
        try:
            divs = _polygon_get('/v3/reference/dividends', {
                'ticker': ticker, 'limit': 8, 'order': 'desc', 'sort': 'pay_date'
            })
            div_results = divs.get('results', [])
            if div_results and current_price:
                annual_div = sum(d.get('cash_amount', 0) for d in div_results[:4])
                div_yield = normalize_dividend_yield(annual_div / current_price)
        except Exception:
            pass

        result = {
            'success': True,
            'ticker': ticker,
            'company_name': company_name,
            'current_price': float(current_price),
            'previous_close': float(prev_close) if prev_close else None,
            'volume': int(volume) if volume else None,
            'dividend_yield': float(div_yield),
            'earnings_date': 'unavailable',
        }
        _cache.set(f'stock_info:{ticker}', result, ttl=300)
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_historical_volatility(ticker, days=30):
    cached = _cache.get(f'hist_vol:{ticker}:{days}')
    if cached is not None:
        return cached
    try:
        end = datetime.now()
        start = end - timedelta(days=days + 10)
        data = _polygon_get(
            f'/v2/aggs/ticker/{ticker}/range/1/day'
            f'/{start.strftime("%Y-%m-%d")}/{end.strftime("%Y-%m-%d")}',
            {'adjusted': 'true', 'sort': 'asc', 'limit': 300}
        )
        results = data.get('results', [])
        if len(results) < 2:
            return None
        closes = np.array([r['c'] for r in results])
        returns = np.log(closes[1:] / closes[:-1])
        volatility = float(returns.std() * np.sqrt(252))
        _cache.set(f'hist_vol:{ticker}:{days}', volatility, ttl=1800)
        return volatility
    except Exception:
        return None


def search_tickers(query, max_results=10):
    if not query:
        return []
    try:
        data = _polygon_get('/v3/reference/tickers', {
            'search': query,
            'active': 'true',
            'market': 'stocks',
            'limit': max_results,
        })
        return [
            {
                'symbol': t.get('ticker', ''),
                'name': t.get('name', ''),
                'exchange': t.get('primary_exchange', ''),
            }
            for t in data.get('results', [])
        ]
    except Exception:
        return []


def get_option_chain(ticker, expiration_date=None):
    try:
        if expiration_date is None:
            exp_result = get_option_expirations(ticker)
            if not exp_result.get('success'):
                return exp_result
            dates = exp_result.get('expirations', [])
            if not dates:
                return {'success': False, 'error': 'No options available'}
            expiration_date = dates[0]

        calls_data, puts_data = [], []
        data = _polygon_get(f'/v3/snapshot/options/{ticker}', {'expiration_date': expiration_date, 'limit': 250})
        while True:
            for opt in data.get('results', []):
                details = opt.get('details', {})
                contract_type = details.get('contract_type', '').lower()
                last_quote = opt.get('last_quote', {})
                day = opt.get('day', {})
                iv = opt.get('implied_volatility') or 0
                row = {
                    'strike': float(details.get('strike_price', 0)),
                    'lastPrice': day.get('close'),
                    'bid': last_quote.get('bid'),
                    'ask': last_quote.get('ask'),
                    'volume': int(day.get('volume') or 0),
                    'openInterest': int(opt.get('open_interest') or 0),
                    'impliedVolatility': normalize_implied_volatility(iv),
                }
                if contract_type == 'call':
                    calls_data.append(row)
                elif contract_type == 'put':
                    puts_data.append(row)
            next_url = data.get('next_url')
            if not next_url:
                break
            data = _polygon_next(next_url)

        calls_data.sort(key=lambda x: x['strike'])
        puts_data.sort(key=lambda x: x['strike'])
        return {
            'success': True,
            'expiration_date': expiration_date,
            'calls': calls_data,
            'puts': puts_data,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


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


def binomial_tree_american(S, K, T, r, sigma, option_type='call', steps=100, q=0):
    """Calculate American option price using binomial tree"""
    if T <= 0:
        if option_type == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    
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


def get_option_expirations(ticker, months=None):
    cache_key = f'opt_exp:{ticker}'
    dates = _cache.get(cache_key)
    if dates is None:
        try:
            today_str = datetime.now().strftime('%Y-%m-%d')
            all_dates = set()
            data = _polygon_get('/v3/reference/options/contracts', {
                'underlying_ticker': ticker,
                'expiration_date.gte': today_str,
                'order': 'asc',
                'sort': 'expiration_date',
                'limit': 250,
            })
            while True:
                for c in data.get('results', []):
                    all_dates.add(c['expiration_date'])
                next_url = data.get('next_url')
                if not next_url:
                    break
                data = _polygon_next(next_url)
            dates = sorted(all_dates)
            if not dates:
                return {'success': False, 'error': 'No options available'}
            _cache.set(cache_key, dates, ttl=3600)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    if months is not None:
        eastern = pytz.timezone('US/Eastern')
        now_et = datetime.now(eastern)
        today = datetime.now()
        cutoff = today + timedelta(days=int(months) * 30)
        filtered = [
            d for d in dates
            if today.date() <= datetime.strptime(d, '%Y-%m-%d').date() <= cutoff.date()
            and not (datetime.strptime(d, '%Y-%m-%d').date() == today.date() and now_et.hour >= 16)
        ]
        return {'success': True, 'expirations': filtered, 'all_expirations': dates}
    return {'success': True, 'expirations': dates}


def get_atm_implied_volatility(ticker, expiration_date, current_price, option_type='call'):
    """Get at-the-money implied volatility for an expiration date"""
    try:
        chain = get_option_chain(ticker, expiration_date)
        if not chain.get('success'):
            return {'success': False, 'error': chain.get('error'), 'implied_volatility': None}
        call_iv, put_iv = None, None
        min_cd, min_pd = float('inf'), float('inf')
        for c in chain['calls']:
            diff = abs(c['strike'] - current_price)
            if diff < min_cd and c['impliedVolatility'] > 0:
                min_cd, call_iv = diff, c['impliedVolatility']
        for p in chain['puts']:
            diff = abs(p['strike'] - current_price)
            if diff < min_pd and p['impliedVolatility'] > 0:
                min_pd, put_iv = diff, p['impliedVolatility']
        if option_type == 'call' and call_iv:
            iv = call_iv
        elif option_type == 'put' and put_iv:
            iv = put_iv
        elif call_iv and put_iv:
            iv = (call_iv + put_iv) / 2
        else:
            iv = call_iv or put_iv
        return {'success': True, 'implied_volatility': iv}
    except Exception as e:
        return {'success': False, 'error': str(e), 'implied_volatility': None}


def get_iv_for_strike(ticker, expiration_date, strike, option_type='call'):
    """Get implied volatility for a specific strike price"""
    try:
        chain = get_option_chain(ticker, expiration_date)
        if not chain.get('success'):
            return {'success': False, 'error': chain.get('error'), 'implied_volatility': None}
        opts = chain['calls'] if option_type == 'call' else chain['puts']
        best, min_diff = None, float('inf')
        for o in opts:
            diff = abs(o['strike'] - float(strike))
            if diff < min_diff:
                min_diff, best = diff, o
        iv = best['impliedVolatility'] if best and best['impliedVolatility'] > 0 else None
        return {'success': True, 'implied_volatility': iv}
    except Exception as e:
        return {'success': False, 'error': str(e), 'implied_volatility': None}


def dispatch_api(tool, args):
    """Dispatch a REST API call to the appropriate business logic function"""
    if tool == 'get_stock_info':
        return get_stock_info(args['ticker'])
    elif tool == 'get_historical_volatility':
        return {'volatility': get_historical_volatility(args['ticker'], int(args.get('days', 30)))}
    elif tool == 'search_tickers':
        return search_tickers(args['query'], int(args.get('max_results', 10)))
    elif tool == 'get_option_chain':
        return get_option_chain(args['ticker'], args.get('expiration_date'))
    elif tool == 'get_option_expirations':
        return get_option_expirations(args['ticker'], args.get('months'))
    elif tool == 'get_atm_implied_volatility':
        return get_atm_implied_volatility(
            args['ticker'], args['expiration_date'],
            float(args['current_price']), args.get('option_type', 'call'))
    elif tool == 'get_implied_volatility_for_strike':
        return get_iv_for_strike(
            args['ticker'], args['expiration_date'],
            float(args['strike']), args.get('option_type', 'call'))
    elif tool == 'calculate_option_price':
        S = float(args['stock_price'])
        K = float(args['strike_price'])
        T = float(args['time_to_expiration'])
        r = float(args['risk_free_rate'])
        sigma = float(args['volatility'])
        option_type = args['option_type']
        model = args.get('model', 'black-scholes')
        q = float(args.get('dividend_yield', 0))
        if model == 'binomial':
            price = binomial_tree_american(S, K, T, r, sigma, option_type, q=q)
        elif option_type == 'call':
            price = black_scholes_call(S, K, T, r, sigma)
        else:
            price = black_scholes_put(S, K, T, r, sigma)
        return {'price': price, 'model': model, 'option_type': option_type}
    elif tool == 'calculate_greeks':
        return calculate_greeks(
            float(args['stock_price']), float(args['strike_price']),
            float(args['time_to_expiration']), float(args['risk_free_rate']),
            float(args['volatility']), args['option_type'])
    else:
        raise ValueError(f'Unknown tool: {tool}')


# ==================== MCP SERVER ====================

server = Server("option-calculator-server")


AUTH_TOKEN_ENV_VARS = ("MCP_SERVER_AUTH_TOKEN", "OPTIONCALC_API_TOKEN")


def get_configured_auth_token():
    for env_var in AUTH_TOKEN_ENV_VARS:
        token = os.environ.get(env_var)
        if token:
            return token
    return None


def is_request_authorized(request: Request) -> bool:
    configured_token = get_configured_auth_token()
    if not configured_token:
        return True

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip() == configured_token

    api_key = request.headers.get("x-api-key", "")
    return api_key == configured_token


async def require_auth(request: Request):
    if is_request_authorized(request):
        return None
    return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)


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
            q = float(arguments.get("dividend_yield", 0))
            
            if model == "binomial":
                price = binomial_tree_american(S, K, T, r, sigma, option_type, q=q)
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


async def handle_api_rest(request: Request):
    unauthorized = await require_auth(request)
    if unauthorized is not None:
        return unauthorized
    try:
        body = await request.json()
        tool = body.get('tool')
        args = body.get('args', {})
        result = dispatch_api(tool, args)
        return JSONResponse({'ok': True, 'result': result})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    unauthorized = await require_auth(request)
    if unauthorized is not None:
        return PlainTextResponse("Unauthorized", status_code=401)
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
    unauthorized = await require_auth(request)
    if unauthorized is not None:
        return unauthorized
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def handle_health(_request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=handle_health),
        Route("/api", endpoint=handle_api_rest, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
