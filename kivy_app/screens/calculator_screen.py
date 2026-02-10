"""
Calculator Screen - Main screen for option pricing calculations
"""

import os
import sys
import threading
from datetime import datetime, timedelta
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label

# Import backend modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import yahoo_data as yd
import option_pricing as bs
from config_manager import ConfigManager
from utils.input_validator import InputValidator


class CalculatorScreen(Screen):
    """Main calculator screen with all option pricing functionality"""
    
    # Observable properties for UI binding
    ticker_text = StringProperty('')
    company_name = StringProperty('Enter a ticker symbol to begin')
    current_price = StringProperty('')
    strike_price = StringProperty('')
    expiration_date = StringProperty('')
    volatility = StringProperty('')
    risk_free_rate = StringProperty('4.5')
    dividend_rate = StringProperty('0.0')
    option_type = StringProperty('call')
    
    # Results
    calculated_price = StringProperty('')
    delta_value = StringProperty('')
    gamma_value = StringProperty('')
    theta_value = StringProperty('')
    vega_value = StringProperty('')
    rho_value = StringProperty('')
    
    # Suggestions
    suggestions = ListProperty([])
    show_suggestions = BooleanProperty(False)
    
    # Loading state
    is_loading = BooleanProperty(False)
    
    # Stock data
    stock_data = None
    expiration_dates = []
    dividend_yield = 0.0
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        # Load saved risk-free rate
        config = self.config_manager.load_config()
        self.risk_free_rate = str(config.get('risk_free_rate', 4.5))
        
        # Initialize validator
        self.validator = InputValidator(self.show_error)
        
    def show_error(self, title, message):
        """Show error popup"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
    
    def show_warning(self, title, message):
        """Show warning popup"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
    
    def on_ticker_input(self, text):
        """Handle ticker input changes"""
        self.ticker_text = text.upper()
        
        if len(text) >= 1:
            # Search for suggestions in background
            threading.Thread(
                target=self._fetch_suggestions,
                args=(text,),
                daemon=True
            ).start()
        else:
            self.suggestions = []
            self.show_suggestions = False
    
    def _fetch_suggestions(self, query):
        """Fetch ticker suggestions (runs in background thread)"""
        try:
            results = yd.search_ticker(query, max_results=10)
            
            # Format suggestions for display
            formatted = []
            for result in results[:10]:  # Limit to 10 entries
                symbol = result['symbol']
                name = result['name']
                # Truncate long names
                if len(name) > 40:
                    name = name[:37] + "..."
                formatted.append({
                    'symbol': symbol,
                    'name': name,
                    'display': f"{symbol} - {name}"
                })
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_suggestions(formatted), 0)
        except Exception as e:
            print(f"Error fetching suggestions: {e}")
    
    def _update_suggestions(self, suggestions):
        """Update suggestions on main thread"""
        self.suggestions = suggestions
        self.show_suggestions = len(suggestions) > 0
    
    def select_suggestion(self, symbol):
        """Handle suggestion selection"""
        self.ticker_text = symbol
        self.show_suggestions = False
        self.load_stock_data()
    
    def load_stock_data(self):
        """Load stock data for the entered ticker"""
        ticker = self.ticker_text.strip().upper()
        
        if not self.validator.validate_ticker(ticker):
            return
        
        self.show_suggestions = False
        self.is_loading = True
        self.company_name = f"Loading data for {ticker}..."
        
        # Fetch data in background
        threading.Thread(
            target=self._fetch_stock_data,
            args=(ticker,),
            daemon=True
        ).start()
    
    def _fetch_stock_data(self, ticker):
        """Fetch stock data (runs in background thread)"""
        try:
            # Get stock data
            stock_data = yd.get_stock_data(ticker)
            
            if stock_data is None:
                Clock.schedule_once(
                    lambda dt: self._on_data_load_error(f"Could not fetch data for {ticker}"),
                    0
                )
                return
            
            # Get expiration dates
            exp_dates = yd.get_expiration_dates(ticker)
            
            # Get dividend yield
            div_yield = yd.get_dividend_yield(ticker)
            
            # Update UI on main thread
            Clock.schedule_once(
                lambda dt: self._on_data_loaded(stock_data, exp_dates, div_yield),
                0
            )
            
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._on_data_load_error(str(e)),
                0
            )
    
    def _on_data_loaded(self, stock_data, exp_dates, div_yield):
        """Handle successful data load (main thread)"""
        self.is_loading = False
        self.stock_data = stock_data
        self.expiration_dates = exp_dates
        self.dividend_yield = div_yield
        
        # Update UI
        self.company_name = stock_data.get('longName', stock_data.get('shortName', self.ticker_text))
        self.current_price = f"{stock_data['currentPrice']:.2f}"
        self.dividend_rate = f"{div_yield * 100:.2f}"
        
        # Set default expiration (30 days out if available)
        if exp_dates:
            target_date = datetime.now() + timedelta(days=30)
            closest_date = min(exp_dates, key=lambda d: abs((datetime.strptime(d, '%Y-%m-%d') - target_date).days))
            self.expiration_date = closest_date
        
        # Calculate historical volatility
        self._calculate_historical_volatility()
    
    def _on_data_load_error(self, error_msg):
        """Handle data load error (main thread)"""
        self.is_loading = False
        self.company_name = "Error loading data"
        self.show_error("Data Load Error", error_msg)
    
    def _calculate_historical_volatility(self):
        """Calculate and set historical volatility"""
        if self.stock_data is None:
            return
        
        try:
            hist_vol = yd.calculate_historical_volatility(self.ticker_text, days=30)
            if hist_vol is not None:
                self.volatility = f"{hist_vol * 100:.2f}"
        except Exception as e:
            print(f"Error calculating volatility: {e}")
            self.volatility = "20.0"  # Default
    
    def calculate_option(self):
        """Calculate option price and Greeks"""
        # Validate inputs
        if not self.current_price or not self.validator.validate_required_field(
            self.current_price, "Current Price"
        ):
            return
        
        if not self.strike_price or not self.validator.validate_required_field(
            self.strike_price, "Strike Price"
        ):
            return
        
        if not self.expiration_date or not self.validator.validate_required_field(
            self.expiration_date, "Expiration Date"
        ):
            return
        
        if not self.volatility or not self.validator.validate_required_field(
            self.volatility, "Volatility"
        ):
            return
        
        try:
            # Parse inputs
            S = float(self.current_price)
            K = float(self.strike_price)
            sigma = float(self.volatility) / 100  # Convert percentage to decimal
            r = float(self.risk_free_rate) / 100  # Convert percentage to decimal
            q = float(self.dividend_rate) / 100  # Convert percentage to decimal
            
            # Calculate time to expiration
            T = yd.get_years_to_expiration(self.expiration_date)
            
            if T <= 0:
                self.show_warning("Invalid Date", "Option has expired or expiration date is invalid")
                return
            
            # Calculate option price using American binomial model
            opt_type = self.option_type.lower()
            price = bs.american_option_binomial(S, K, T, r, sigma, q=q, option_type=opt_type, steps=100)
            
            # Calculate Greeks
            greeks = bs.calculate_greeks(S, K, T, r, sigma, opt_type)
            
            # Update results
            self.calculated_price = f"${price:.2f}"
            self.delta_value = f"{greeks['delta']:.4f}"
            self.gamma_value = f"{greeks['gamma']:.4f}"
            self.theta_value = f"{greeks['theta']:.4f}"
            self.vega_value = f"{greeks['vega']:.4f}"
            self.rho_value = f"{greeks['rho']:.4f}"
            
        except ValueError:
            self.show_error("Input Error", "Please ensure all numeric fields are filled with valid numbers")
        except Exception as e:
            self.show_error("Calculation Error", f"An error occurred: {str(e)}")
    
    def save_risk_free_rate(self):
        """Save risk-free rate to config"""
        try:
            rate = float(self.risk_free_rate)
            config = self.config_manager.load_config()
            config['risk_free_rate'] = rate
            self.config_manager.save_config(config)
        except ValueError:
            pass  # Invalid input, don't save
    
    def toggle_option_type(self):
        """Toggle between call and put"""
        self.option_type = 'put' if self.option_type == 'call' else 'call'
