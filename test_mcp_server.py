"""
Test script for MCP Server
Run this to verify your MCP server is working correctly
"""

import json
import sys
from mcp_client import MCPClient


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(result):
    """Print result in a formatted way"""
    print(json.dumps(result, indent=2))
    print()


def test_stock_info(client):
    """Test get_stock_info tool"""
    print_header("Test 1: Get Stock Info for AAPL")
    try:
        result = client.get_stock_info("AAPL")
        if result.get("success"):
            print("✓ SUCCESS")
            print(f"Company: {result.get('company_name')}")
            print(f"Price: ${result.get('current_price'):.2f}")
            print(f"Dividend Yield: {result.get('dividend_yield', 0) * 100:.2f}%")
        else:
            print("✗ FAILED")
            print(f"Error: {result.get('error')}")
        return result.get("success", False)
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def test_option_pricing(client):
    """Test calculate_option_price tool"""
    print_header("Test 2: Calculate Call Option Price")
    try:
        result = client.calculate_option_price(
            stock_price=150.0,
            strike_price=155.0,
            time_to_expiration=0.25,  # 3 months
            risk_free_rate=0.05,
            volatility=0.30,
            option_type="call",
            model="black-scholes"
        )
        if "price" in result:
            print("✓ SUCCESS")
            print(f"Call Option Price: ${result['price']:.2f}")
            print(f"Model: {result.get('model')}")
        else:
            print("✗ FAILED")
            print(f"Error: {result.get('error')}")
        return "price" in result
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def test_greeks(client):
    """Test calculate_greeks tool"""
    print_header("Test 3: Calculate Greeks")
    try:
        result = client.calculate_greeks(
            stock_price=150.0,
            strike_price=155.0,
            time_to_expiration=0.25,
            risk_free_rate=0.05,
            volatility=0.30,
            option_type="call"
        )
        if "delta" in result:
            print("✓ SUCCESS")
            print(f"Delta: {result['delta']:.4f}")
            print(f"Gamma: {result['gamma']:.4f}")
            print(f"Theta: {result['theta']:.4f}")
            print(f"Vega: {result['vega']:.4f}")
            print(f"Rho: {result['rho']:.4f}")
        else:
            print("✗ FAILED")
            print(f"Error: {result.get('error')}")
        return "delta" in result
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def test_historical_volatility(client):
    """Test get_historical_volatility tool"""
    print_header("Test 4: Get Historical Volatility")
    try:
        result = client.get_historical_volatility("AAPL", days=30)
        if result.get("volatility") is not None:
            print("✓ SUCCESS")
            print(f"Ticker: {result.get('ticker')}")
            print(f"Days: {result.get('days')}")
            print(f"Volatility: {result.get('volatility') * 100:.2f}%")
        else:
            print("✗ FAILED")
            print(f"Error: {result.get('error')}")
        return result.get("volatility") is not None
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def test_search_tickers(client):
    """Test search_tickers tool"""
    print_header("Test 5: Search Tickers")
    try:
        result = client.search_tickers("apple", max_results=3)
        if isinstance(result, list) and len(result) > 0:
            print("✓ SUCCESS")
            print(f"Found {len(result)} results:")
            for ticker in result[:3]:
                print(f"  - {ticker.get('symbol')}: {ticker.get('name')}")
        else:
            print("✗ FAILED")
            print(f"No results or error")
        return isinstance(result, list) and len(result) > 0
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def test_binomial_model(client):
    """Test binomial tree model"""
    print_header("Test 6: Binomial Tree (American Option)")
    try:
        result = client.calculate_option_price(
            stock_price=150.0,
            strike_price=155.0,
            time_to_expiration=0.25,
            risk_free_rate=0.05,
            volatility=0.30,
            option_type="put",
            model="binomial"
        )
        if "price" in result:
            print("✓ SUCCESS")
            print(f"American Put Option Price: ${result['price']:.2f}")
            print(f"Model: {result.get('model')}")
        else:
            print("✗ FAILED")
            print(f"Error: {result.get('error')}")
        return "price" in result
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  MCP Server Test Suite")
    print("=" * 60)
    print("\nThis will test all MCP server tools...")
    print("Make sure the MCP server is running!\n")
    
    # Initialize client
    print("Initializing MCP client (local mode)...")
    try:
        client = MCPClient("python mcp-server/server.py")
        print("✓ Client initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return
    
    # Run tests
    results = []
    results.append(("Stock Info", test_stock_info(client)))
    results.append(("Option Pricing (Black-Scholes)", test_option_pricing(client)))
    results.append(("Greeks Calculation", test_greeks(client)))
    results.append(("Historical Volatility", test_historical_volatility(client)))
    results.append(("Ticker Search", test_search_tickers(client)))
    results.append(("Binomial Model", test_binomial_model(client)))
    
    # Print summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your MCP server is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
