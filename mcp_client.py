"""
MCP Client for Option Calculator
Connects to the MCP server and provides a simple interface for tool calls
"""

import json
import subprocess
import sys
from typing import Optional, Dict, Any


class MCPClient:
    """Client to interact with the Option Calculator MCP Server"""
    
    def __init__(self, server_command: str = ".venv\\Scripts\\python.exe mcp-server\\server.py"):
        """
        Initialize MCP Client
        
        Args:
            server_command: Command to start the MCP server (local) or server URL (Railway)
        """
        self.server_command = server_command
        self.is_local = "python" in server_command or "node" in server_command
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Dictionary containing the tool's response
        """
        if self.is_local:
            return self._call_local_tool(tool_name, arguments)
        else:
            return self._call_remote_tool(tool_name, arguments)
    
    def _call_local_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on local MCP server via stdio"""
        try:
            # Prepare MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Start server process
            process = subprocess.Popen(
                self.server_command.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send request
            stdout, stderr = process.communicate(
                input=json.dumps(request) + "\n",
                timeout=30
            )
            
            if stderr:
                return {"success": False, "error": f"Server error: {stderr}"}
            
            # Parse response
            try:
                response = json.loads(stdout)
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"]
                    if isinstance(content, list) and len(content) > 0:
                        return json.loads(content[0]["text"])
                return response
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON response: {e}"}
        
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _call_remote_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on remote MCP server (Railway)"""
        # For Railway deployment, you would use an HTTP client or WebSocket
        # This is a placeholder for the remote implementation
        import requests
        
        try:
            response = requests.post(
                f"{self.server_command}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                },
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Convenience methods for each tool
    
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """Get stock information"""
        return self.call_tool("get_stock_info", {"ticker": ticker})
    
    def calculate_option_price(
        self,
        stock_price: float,
        strike_price: float,
        time_to_expiration: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str = "call",
        model: str = "black-scholes"
    ) -> Dict[str, Any]:
        """Calculate option price"""
        return self.call_tool("calculate_option_price", {
            "stock_price": stock_price,
            "strike_price": strike_price,
            "time_to_expiration": time_to_expiration,
            "risk_free_rate": risk_free_rate,
            "volatility": volatility,
            "option_type": option_type,
            "model": model
        })
    
    def calculate_greeks(
        self,
        stock_price: float,
        strike_price: float,
        time_to_expiration: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        """Calculate option Greeks"""
        return self.call_tool("calculate_greeks", {
            "stock_price": stock_price,
            "strike_price": strike_price,
            "time_to_expiration": time_to_expiration,
            "risk_free_rate": risk_free_rate,
            "volatility": volatility,
            "option_type": option_type
        })
    
    def get_historical_volatility(self, ticker: str, days: int = 30) -> Dict[str, Any]:
        """Get historical volatility"""
        return self.call_tool("get_historical_volatility", {
            "ticker": ticker,
            "days": days
        })
    
    def search_tickers(self, query: str, max_results: int = 10) -> list:
        """Search for tickers"""
        result = self.call_tool("search_tickers", {
            "query": query,
            "max_results": max_results
        })
        # Return the list directly if successful
        if isinstance(result, list):
            return result
        return []
    
    def get_option_chain(self, ticker: str, expiration_date: Optional[str] = None) -> Dict[str, Any]:
        """Get option chain"""
        args = {"ticker": ticker}
        if expiration_date:
            args["expiration_date"] = expiration_date
        return self.call_tool("get_option_chain", args)


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = MCPClient()
    
    # Test get stock info
    print("Getting stock info for AAPL...")
    result = client.get_stock_info("AAPL")
    print(json.dumps(result, indent=2))
    
    # Test option pricing
    print("\nCalculating call option price...")
    result = client.calculate_option_price(
        stock_price=150.0,
        strike_price=155.0,
        time_to_expiration=0.25,
        risk_free_rate=0.05,
        volatility=0.30,
        option_type="call"
    )
    print(json.dumps(result, indent=2))
    
    # Test Greeks
    print("\nCalculating Greeks...")
    result = client.calculate_greeks(
        stock_price=150.0,
        strike_price=155.0,
        time_to_expiration=0.25,
        risk_free_rate=0.05,
        volatility=0.30,
        option_type="call"
    )
    print(json.dumps(result, indent=2))
