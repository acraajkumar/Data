"""
Greeks calculations for options.

This module provides a Greeks dataclass and utilities for calculating
option sensitivities.
"""

from dataclasses import dataclass
from typing import Optional

from .option import Option
from .black_scholes import BlackScholes


@dataclass
class Greeks:
    """
    Container for option Greeks (sensitivities).
    
    Attributes:
        delta: Rate of change of option price with respect to underlying price
        gamma: Rate of change of delta with respect to underlying price
        theta: Rate of change of option price with respect to time (per year)
        vega: Rate of change of option price with respect to volatility (per 1%)
        rho: Rate of change of option price with respect to interest rate (per 1%)
    """
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    
    @classmethod
    def calculate(cls, option: Option) -> "Greeks":
        """
        Calculate all Greeks for an option.
        
        Args:
            option: Option contract to calculate Greeks for
            
        Returns:
            Greeks instance with all calculated values
        """
        return cls(
            delta=BlackScholes.delta(option),
            gamma=BlackScholes.gamma(option),
            theta=BlackScholes.theta(option),
            vega=BlackScholes.vega(option),
            rho=BlackScholes.rho(option)
        )
    
    @property
    def theta_daily(self) -> float:
        """Return theta expressed as daily decay (theta/365)."""
        return self.theta / 365
    
    def __str__(self) -> str:
        """Return formatted string representation of Greeks."""
        return (
            f"Greeks(\n"
            f"  Delta: {self.delta:+.4f}\n"
            f"  Gamma: {self.gamma:.6f}\n"
            f"  Theta: {self.theta:.4f}/year ({self.theta_daily:.4f}/day)\n"
            f"  Vega:  {self.vega:.4f}/1%\n"
            f"  Rho:   {self.rho:.4f}/1%\n"
            f")"
        )


def calculate_portfolio_greeks(positions: list) -> Greeks:
    """
    Calculate aggregate Greeks for a portfolio of positions.
    
    Args:
        positions: List of tuples (Option, quantity) where quantity 
                   is positive for long, negative for short
                   
    Returns:
        Aggregate Greeks for the entire portfolio
    """
    total_delta = 0.0
    total_gamma = 0.0
    total_theta = 0.0
    total_vega = 0.0
    total_rho = 0.0
    
    for option, quantity in positions:
        greeks = Greeks.calculate(option)
        total_delta += greeks.delta * quantity
        total_gamma += greeks.gamma * quantity
        total_theta += greeks.theta * quantity
        total_vega += greeks.vega * quantity
        total_rho += greeks.rho * quantity
    
    return Greeks(
        delta=total_delta,
        gamma=total_gamma,
        theta=total_theta,
        vega=total_vega,
        rho=total_rho
    )
