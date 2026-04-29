"""
Proxy client for the Railway MCP server.
Provides the same API surface as yahoo_data.py and option_pricing.py so both
UIs only need to change their import lines.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def _load_json_config():
    config_candidates = [
        Path.cwd() / 'config.json',
        Path(__file__).resolve().parent / 'config.json',
    ]

    for config_path in config_candidates:
        if not config_path.exists():
            continue
        try:
            return json.loads(config_path.read_text())
        except Exception:
            continue
    return {}


_JSON_CONFIG = _load_json_config()


def _config_value(*keys, default=None):
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
        value = _JSON_CONFIG.get(key)
        if value:
            return value
    return default


_SERVER_URL = _config_value('MCP_SERVER_URL', 'mcp_server_url', default='http://localhost:8080').rstrip('/')
_SERVER_AUTH_TOKEN = _config_value('MCP_SERVER_AUTH_TOKEN', 'OPTIONCALC_API_TOKEN', 'mcp_server_auth_token')


def _headers():
    if not _SERVER_AUTH_TOKEN:
        return {}
    return {
        'Authorization': f'Bearer {_SERVER_AUTH_TOKEN}',
        'X-API-Key': _SERVER_AUTH_TOKEN,
    }


def _call(tool, **args):
    resp = requests.post(
        f'{_SERVER_URL}/api',
        json={'tool': tool, 'args': args},
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise RuntimeError(data.get('error', 'Server error'))
    return data['result']


# ── Date utilities (pure math — no network call needed) ────────

def get_days_to_expiration(expiration_date_str):
    try:
        exp = datetime.strptime(expiration_date_str, '%Y-%m-%d')
        return max((exp - datetime.now()).days, 0)
    except Exception:
        return 0


def get_years_to_expiration(expiration_date_str):
    return get_days_to_expiration(expiration_date_str) / 365.0


# ── Stock data ─────────────────────────────────────────────────

def search_ticker(query, max_results=10):
    """Returns list of {symbol, name, exchange, type} dicts"""
    return _call('search_tickers', query=query, max_results=max_results)


def get_stock_info(ticker):
    """Returns {success, ticker, current_price, company_name, ...}"""
    return _call('get_stock_info', ticker=ticker)


def get_stock_data(ticker):
    """Kivy-compatible variant — returns raw stock dict or None on failure"""
    result = _call('get_stock_info', ticker=ticker)
    if not result.get('success'):
        return None
    return {
        'currentPrice': result['current_price'],
        'longName': result.get('company_name', ticker),
        'shortName': result.get('company_name', ticker),
        'previousClose': result.get('previous_close'),
        'volume': result.get('volume'),
        'dividendYield': result.get('dividend_yield', 0),
    }


def get_dividend_yield(ticker):
    """Kivy-compatible variant — returns dividend yield as decimal"""
    result = _call('get_stock_info', ticker=ticker)
    return result.get('dividend_yield', 0)


_PERIOD_DAYS = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '2y': 730, '5y': 1825}


def calculate_historical_volatility(ticker, period=None, days=None):
    """Accepts either a period string ('1y', '6mo') or a days integer"""
    if days is None:
        days = _PERIOD_DAYS.get(period or '1y', 365)
    result = _call('get_historical_volatility', ticker=ticker, days=days)
    return result.get('volatility')


# ── Option chain ───────────────────────────────────────────────

def get_option_chain(ticker):
    """Returns {success, expirations} — full list of expiration date strings"""
    return _call('get_option_expirations', ticker=ticker)


def get_option_chain_next_months(ticker, months=6):
    """Returns {success, expirations} filtered to next N months"""
    return _call('get_option_expirations', ticker=ticker, months=months)


def get_expiration_dates(ticker):
    """Kivy-compatible variant — returns list of expiration date strings"""
    result = _call('get_option_expirations', ticker=ticker, months=6)
    return result.get('expirations', [])


def get_options_for_expiration(ticker, expiration_date):
    """Returns {success, calls, puts} with snake_case field names"""
    result = _call('get_option_chain', ticker=ticker, expiration_date=expiration_date)
    if not result.get('success'):
        return result

    def _normalize(opts):
        return [{
            'strike': o['strike'],
            'last_price': o.get('lastPrice'),
            'bid': o.get('bid'),
            'ask': o.get('ask'),
            'volume': o.get('volume', 0),
            'open_interest': o.get('openInterest', 0),
            'implied_volatility': o.get('impliedVolatility', 0),
        } for o in opts]

    return {
        'success': True,
        'expiration': expiration_date,
        'calls': _normalize(result.get('calls', [])),
        'puts': _normalize(result.get('puts', [])),
    }


def get_implied_volatility_for_strike(ticker, expiration_date, strike, option_type='call'):
    """Returns IV as decimal or None"""
    result = _call('get_implied_volatility_for_strike',
                   ticker=ticker, expiration_date=expiration_date,
                   strike=strike, option_type=option_type)
    return result.get('implied_volatility')


def get_atm_implied_volatility(ticker, expiration_date, current_price, option_type='call'):
    """Returns ATM IV as decimal or None"""
    result = _call('get_atm_implied_volatility',
                   ticker=ticker, expiration_date=expiration_date,
                   current_price=current_price, option_type=option_type)
    return result.get('implied_volatility')


# ── Option pricing ─────────────────────────────────────────────

def american_option_binomial(S, K, T, r, sigma, q=0, option_type='call', steps=100):
    result = _call('calculate_option_price',
                   stock_price=S, strike_price=K, time_to_expiration=T,
                   risk_free_rate=r, volatility=sigma, option_type=option_type,
                   model='binomial', dividend_yield=q)
    return result.get('price', 0.0)


def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    return _call('calculate_greeks',
                 stock_price=S, strike_price=K, time_to_expiration=T,
                 risk_free_rate=r, volatility=sigma, option_type=option_type)
