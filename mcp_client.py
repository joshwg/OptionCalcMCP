"""
MCP Client for Option Calculator
Connects to the HTTP API exposed by the Option Calculator server.
"""

import os
import shlex
import socket
import subprocess
import sys
import time
from contextlib import closing
from typing import Optional, Dict, Any

import requests


class MCPClient:
    """Client to interact with the Option Calculator server."""
    
    def __init__(self, server_command: Optional[str] = None):
        """
        Initialize MCP Client
        
        Args:
            server_command: Command to start the MCP server (local) or server URL (Railway)
        """
        if server_command is None:
            server_command = f'"{sys.executable}" mcp-server\\server.py'

        self.server_command = server_command
        self.is_local = not server_command.startswith(("http://", "https://"))
        self.base_url = self._resolve_base_url(server_command)
    
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
        return self._call_remote_tool(tool_name, arguments)

    def _resolve_base_url(self, server_command: str) -> str:
        if self.is_local:
            port = int(os.getenv("MCP_SERVER_PORT", "8080"))
            return f"http://127.0.0.1:{port}"
        return server_command.rstrip("/")

    def _pick_unused_port(self) -> int:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _command_args(self) -> list[str]:
        return [part.strip('"') for part in shlex.split(self.server_command, posix=False)]

    def _wait_for_server(self, base_url: str, timeout: float = 10.0) -> None:
        deadline = time.time() + timeout
        last_error = None
        while time.time() < deadline:
            try:
                response = requests.get(f"{base_url}/health", timeout=1)
                if response.ok:
                    return
            except requests.RequestException as exc:
                last_error = exc
            time.sleep(0.2)
        raise RuntimeError(f"Server did not become ready at {base_url}: {last_error}")

    def _post_api(self, base_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{base_url}/api",
            json={"tool": tool_name, "args": arguments},
            timeout=30
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            return {"success": False, "error": payload.get("error", "Unknown server error")}
        return payload["result"]
    
    def _call_local_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on a local server process via HTTP."""
        port = self._pick_unused_port()
        base_url = f"http://127.0.0.1:{port}"
        process = None
        try:
            env = os.environ.copy()
            env["PORT"] = str(port)
            process = subprocess.Popen(
                self._command_args(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            self._wait_for_server(base_url)
            return self._post_api(base_url, tool_name, arguments)
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    
    def _call_remote_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on remote server via the REST API."""
        try:
            return self._post_api(self.base_url, tool_name, arguments)
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
