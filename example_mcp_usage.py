"""
Example: Converting Existing Calculator to Use MCP Client

This file shows how to modify calculator_operations.py to use the MCP server
instead of direct function calls.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from mcp_client import MCPClient
from utils import ThreadingHelper, InputValidator


class CalculatorOperations:
    """
    Example of calculator operations using MCP client
    Replace direct imports with MCP tool calls
    """
    
    def __init__(self):
        """Initialize with MCP client"""
        # Initialize MCP client
        # For local development:
        self.mcp_client = MCPClient("python mcp-server/server.py")
        
        # For production (Railway):
        # self.mcp_client = MCPClient("https://your-app.railway.app")
        
        # Or use environment variable:
        # import os
        # server_url = os.getenv("MCP_SERVER_URL", "python mcp-server/server.py")
        # self.mcp_client = MCPClient(server_url)
    
    
    def load_stock_data(self):
        """
        Load stock data using MCP server
        
        BEFORE (Direct Import):
            import yahoo_data as yd
            info = yd.get_stock_info(ticker)
        
        AFTER (MCP Client):
            info = self.mcp_client.get_stock_info(ticker)
        """
        ticker = InputValidator.validate_ticker(self.ticker.get())
        if not ticker:
            return
        
        self.hide_suggestions()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Loading data for {ticker}...\n")
        
        def fetch_data():
            # MCP CLIENT CALL - replaces yd.get_stock_info()
            info = self.mcp_client.get_stock_info(ticker)
            
            if info.get('success'):
                current_price = info['current_price']
                self.current_price.set(str(current_price))
                self.dividend_yield = info.get('dividend_yield', 0) or 0
                div_yield_pct = self.dividend_yield * 100
                self.dividend_rate.set(f"{div_yield_pct:.2f}")
                earnings_date = info.get('earnings_date') or "unavailable"
                self.earnings_date.set(earnings_date)
                self.window.title(f"Option Calculator - {info['company_name']} ({ticker})")
                
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Company: {info['company_name']}\n")
                self.results_text.insert(tk.END, f"Current Price: ${current_price:.2f}\n")
                self.results_text.insert(tk.END, f"Previous Close: ${info.get('previous_close', 'N/A')}\n")
                self.results_text.insert(tk.END, f"Volume: {info.get('volume', 'N/A')}\n")
                self.results_text.insert(tk.END, f"Dividend Yield: {div_yield_pct:.2f}%\n")
                self.results_text.insert(tk.END, f"Earnings Date: {earnings_date}\n")
            else:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Error: {info.get('error', 'Unknown error')}\n")
        
        ThreadingHelper.run_in_thread(fetch_data)
    
    
    def calculate_option_price(self):
        """
        Calculate option price using MCP server
        
        BEFORE (Direct Import):
            import option_pricing as bs
            call_price = bs.black_scholes_call(S, K, T, r, sigma)
            put_price = bs.black_scholes_put(S, K, T, r, sigma)
        
        AFTER (MCP Client):
            call_result = self.mcp_client.calculate_option_price(...)
            call_price = call_result['price']
        """
        try:
            # Validate inputs
            S = float(self.current_price.get())
            K = float(self.strike_price.get())
            r = float(self.risk_free_rate.get()) / 100
            sigma = float(self.volatility.get()) / 100
            
            # Calculate time to expiration
            exp_date_str = self.expiration_date.get()
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
            T = (exp_date - datetime.now()).days / 365.0
            
            if T <= 0:
                messagebox.showerror("Error", "Expiration date must be in the future")
                return
            
            # Get selected model
            model_text = self.pricing_model.get()
            if "Binomial" in model_text:
                model = "binomial"
            else:
                model = "black-scholes"
            
            # MCP CLIENT CALLS - replace bs.black_scholes_call/put()
            call_result = self.mcp_client.calculate_option_price(
                stock_price=S,
                strike_price=K,
                time_to_expiration=T,
                risk_free_rate=r,
                volatility=sigma,
                option_type="call",
                model=model
            )
            call_price = call_result.get('price', 0)
            
            put_result = self.mcp_client.calculate_option_price(
                stock_price=S,
                strike_price=K,
                time_to_expiration=T,
                risk_free_rate=r,
                volatility=sigma,
                option_type="put",
                model=model
            )
            put_price = put_result.get('price', 0)
            
            # Calculate Greeks using MCP
            call_greeks = self.mcp_client.calculate_greeks(
                stock_price=S,
                strike_price=K,
                time_to_expiration=T,
                risk_free_rate=r,
                volatility=sigma,
                option_type="call"
            )
            
            put_greeks = self.mcp_client.calculate_greeks(
                stock_price=S,
                strike_price=K,
                time_to_expiration=T,
                risk_free_rate=r,
                volatility=sigma,
                option_type="put"
            )
            
            # Display results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Model: {model.title()}\n")
            self.results_text.insert(tk.END, f"Stock Price: ${S:.2f}\n")
            self.results_text.insert(tk.END, f"Strike Price: ${K:.2f}\n")
            self.results_text.insert(tk.END, f"Time to Expiration: {T:.4f} years\n\n")
            
            # Call option
            self.results_text.insert(tk.END, "CALL OPTION:\n")
            self.results_text.insert(tk.END, f"  Price: ${call_price:.2f}\n")
            self.results_text.insert(tk.END, f"  Delta: {call_greeks['delta']:.4f}\n")
            self.results_text.insert(tk.END, f"  Gamma: {call_greeks['gamma']:.4f}\n")
            self.results_text.insert(tk.END, f"  Theta: {call_greeks['theta']:.4f}\n")
            self.results_text.insert(tk.END, f"  Vega: {call_greeks['vega']:.4f}\n")
            self.results_text.insert(tk.END, f"  Rho: {call_greeks['rho']:.4f}\n\n")
            
            # Put option
            self.results_text.insert(tk.END, "PUT OPTION:\n")
            self.results_text.insert(tk.END, f"  Price: ${put_price:.2f}\n")
            self.results_text.insert(tk.END, f"  Delta: {put_greeks['delta']:.4f}\n")
            self.results_text.insert(tk.END, f"  Gamma: {put_greeks['gamma']:.4f}\n")
            self.results_text.insert(tk.END, f"  Theta: {put_greeks['theta']:.4f}\n")
            self.results_text.insert(tk.END, f"  Vega: {put_greeks['vega']:.4f}\n")
            self.results_text.insert(tk.END, f"  Rho: {put_greeks['rho']:.4f}\n")
            
        except ValueError as e:
            messagebox.showerror("Input Error", "Please enter valid numeric values")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
    
    
    def load_historical_volatility(self):
        """
        Load historical volatility using MCP server
        
        BEFORE (Direct Import):
            import yahoo_data as yd
            volatility = yd.get_historical_volatility(ticker, days)
        
        AFTER (MCP Client):
            result = self.mcp_client.get_historical_volatility(ticker, days)
            volatility = result.get('volatility')
        """
        ticker = InputValidator.validate_ticker(self.ticker.get())
        if not ticker:
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Calculating historical volatility for {ticker}...\n")
        
        def fetch_volatility():
            # MCP CLIENT CALL - replaces yd.get_historical_volatility()
            result = self.mcp_client.get_historical_volatility(ticker, days=30)
            
            volatility = result.get('volatility')
            if volatility:
                vol_percent = volatility * 100
                self.volatility.set(f"{vol_percent:.2f}")
                self.results_text.insert(tk.END, f"30-day Historical Volatility: {vol_percent:.2f}%\n")
            else:
                self.results_text.insert(tk.END, "Could not calculate historical volatility\n")
        
        ThreadingHelper.run_in_thread(fetch_volatility)
    
    
    def search_ticker(self, query):
        """
        Search for tickers using MCP server
        
        BEFORE (Direct Import):
            import yahoo_data as yd
            results = yd.search_tickers(query)
        
        AFTER (MCP Client):
            results = self.mcp_client.search_tickers(query)
        """
        if len(query) < 2:
            return []
        
        # MCP CLIENT CALL - replaces yd.search_tickers()
        results = self.mcp_client.search_tickers(query, max_results=10)
        
        if isinstance(results, list):
            return [(r['symbol'], r['name']) for r in results]
        return []


# USAGE EXAMPLE
if __name__ == "__main__":
    """
    This shows how to use the MCP-enabled calculator operations
    """
    
    # Create a simple test
    calc_ops = CalculatorOperations()
    
    # Example 1: Get stock info
    print("Testing stock info...")
    info = calc_ops.mcp_client.get_stock_info("AAPL")
    print(f"Stock: {info.get('company_name')}")
    print(f"Price: ${info.get('current_price'):.2f}")
    
    # Example 2: Calculate option price
    print("\nTesting option pricing...")
    result = calc_ops.mcp_client.calculate_option_price(
        stock_price=150.0,
        strike_price=155.0,
        time_to_expiration=0.25,
        risk_free_rate=0.05,
        volatility=0.30,
        option_type="call",
        model="black-scholes"
    )
    print(f"Call Price: ${result.get('price'):.2f}")
    
    # Example 3: Search tickers
    print("\nTesting ticker search...")
    results = calc_ops.mcp_client.search_tickers("apple", max_results=3)
    for ticker in results[:3]:
        print(f"  {ticker['symbol']}: {ticker['name']}")
