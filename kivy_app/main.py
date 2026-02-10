"""
Kivy Option Calculator - Main Application Entry Point
Android-compatible single-screen option pricing calculator
"""

import os
import sys

# Configure Kivy for WSL2 compatibility (suppress MTDev warning)
os.environ['KIVY_INPUT'] = 'mouse'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.utils import platform

# Add parent directory to path to import backend modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from screens.calculator_screen import CalculatorScreen


class OptionCalculatorApp(App):
    """Main Kivy application for Option Calculator"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Option Calculator"
        
    def build(self):
        """Build and return the root widget"""
        # Set window size for desktop testing (ignored on Android)
        if platform not in ('android', 'ios'):
            Window.size = (400, 800)  # Phone-like dimensions for testing
        
        # Create screen manager
        sm = ScreenManager()
        
        # Add calculator screen
        calculator = CalculatorScreen(name='calculator')
        sm.add_widget(calculator)
        
        return sm
    
    def on_start(self):
        """Called when the application starts"""
        print("Option Calculator started")
    
    def on_pause(self):
        """Called when app is paused (Android)"""
        # Save any pending data
        return True  # Return True to allow pause
    
    def on_resume(self):
        """Called when app resumes from pause (Android)"""
        print("App resumed")


if __name__ == '__main__':
    OptionCalculatorApp().run()
