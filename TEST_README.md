# Black-Scholes Option Calculator - Test Suite

This directory contains comprehensive unit tests for the option calculator application.

## Test Files

### test_yahoo_data.py
Tests for Yahoo Finance data fetching functionality:
- **TestTickerSearch**: Ticker search functionality with various queries
- **TestStockInfo**: Stock information download and validation
- **TestHistoricalVolatility**: Historical volatility calculations
- **TestOptionChain**: Option chain retrieval and structure
- **TestDateCalculations**: Date and time utility functions
- **TestIntegration**: End-to-end workflow tests

### test_black_scholes.py
Tests for Black-Scholes pricing and Greeks:
- **TestBlackScholesCall**: Call option pricing calculations
- **TestBlackScholesPut**: Put option pricing calculations
- **TestPutCallParity**: Put-call parity validation
- **TestGreeks**: Greeks (Delta, Gamma, Theta, Vega, Rho) calculations
- **TestImpliedVolatility**: Implied volatility recovery
- **TestEdgeCases**: Boundary conditions and edge cases

## Running Tests

### Run all tests for Yahoo data module:
```powershell
python test_yahoo_data.py
```

### Run all tests for Black-Scholes module:
```powershell
python test_black_scholes.py
```

### Run specific test class:
```powershell
python -m unittest test_yahoo_data.TestTickerSearch
```

### Run specific test method:
```powershell
python -m unittest test_yahoo_data.TestTickerSearch.test_search_ticker_apple
```

### Run with verbose output:
```powershell
python -m unittest discover -v
```

## Test Coverage

### Yahoo Data Tests (test_yahoo_data.py)
- ✓ Ticker search with valid queries
- ✓ Ticker search with partial matches
- ✓ Empty and invalid query handling
- ✓ Max results limit enforcement
- ✓ Network error handling
- ✓ Stock information retrieval
- ✓ Historical volatility calculation
- ✓ Option chain retrieval
- ✓ Date calculations
- ✓ Integration workflows

### Black-Scholes Tests (test_black_scholes.py)
- ✓ Call/Put option pricing
- ✓ In-the-money, at-the-money, out-of-the-money scenarios
- ✓ Expiration handling (T=0)
- ✓ Put-call parity verification
- ✓ Greeks calculations and ranges
- ✓ Implied volatility recovery
- ✓ Edge cases (low/high volatility, short time, zero rates)

## Test Requirements

All tests use Python's built-in `unittest` framework. Some tests require:
- Active internet connection (for Yahoo Finance API tests)
- numpy and scipy (for numerical calculations)

## Notes

- Network-dependent tests may fail if Yahoo Finance API is unavailable
- Some tests use mocking to avoid network dependencies
- Tests include both unit tests and integration tests
- Edge case tests ensure robustness of calculations
