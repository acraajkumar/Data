"""
Options Trading System

A comprehensive Python-based options trading system with:
- Black-Scholes pricing model
- Greeks calculations (Delta, Gamma, Theta, Vega, Rho)
- Trading strategies
- Portfolio management
- ML-based prediction capabilities
"""

__version__ = "1.0.0"
__author__ = "Options Trading System"

from .models.black_scholes import BlackScholes
from .models.option import Option, OptionType
from .models.greeks import Greeks
from .strategies.strategy import Strategy, StrategyType
from .portfolio import Portfolio

__all__ = [
    "BlackScholes",
    "Option",
    "OptionType",
    "Greeks",
    "Strategy",
    "StrategyType",
    "Portfolio",
]
