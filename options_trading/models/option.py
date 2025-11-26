"""
Option class and related enumerations.

This module provides the core Option class representing a financial option contract.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class OptionType(Enum):
    """Enumeration for option types."""
    CALL = "call"
    PUT = "put"


@dataclass
class Option:
    """
    Represents a financial option contract.
    
    Attributes:
        underlying_price: Current price of the underlying asset
        strike_price: Strike price of the option
        time_to_expiry: Time to expiration in years
        risk_free_rate: Risk-free interest rate (annualized, as decimal)
        volatility: Implied volatility (annualized, as decimal)
        option_type: Type of option (CALL or PUT)
        dividend_yield: Continuous dividend yield (optional, default 0)
    """
    underlying_price: float
    strike_price: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    option_type: OptionType
    dividend_yield: float = 0.0
    
    def __post_init__(self):
        """Validate option parameters after initialization."""
        if self.underlying_price <= 0:
            raise ValueError("Underlying price must be positive")
        if self.strike_price <= 0:
            raise ValueError("Strike price must be positive")
        if self.time_to_expiry < 0:
            raise ValueError("Time to expiry cannot be negative")
        if self.volatility < 0:
            raise ValueError("Volatility cannot be negative")
        if self.dividend_yield < 0:
            raise ValueError("Dividend yield cannot be negative")
    
    @property
    def is_call(self) -> bool:
        """Check if option is a call option."""
        return self.option_type == OptionType.CALL
    
    @property
    def is_put(self) -> bool:
        """Check if option is a put option."""
        return self.option_type == OptionType.PUT
    
    @property
    def moneyness(self) -> float:
        """
        Calculate moneyness ratio (S/K).
        
        Returns:
            Moneyness ratio where:
            - > 1: In-the-money for calls, Out-of-the-money for puts
            - = 1: At-the-money
            - < 1: Out-of-the-money for calls, In-the-money for puts
        """
        return self.underlying_price / self.strike_price
    
    @property
    def intrinsic_value(self) -> float:
        """
        Calculate the intrinsic value of the option.
        
        Returns:
            Intrinsic value (non-negative)
        """
        if self.is_call:
            return max(0, self.underlying_price - self.strike_price)
        return max(0, self.strike_price - self.underlying_price)
    
    def is_in_the_money(self) -> bool:
        """Check if option is in the money."""
        if self.is_call:
            return self.underlying_price > self.strike_price
        return self.underlying_price < self.strike_price
    
    def is_at_the_money(self, tolerance: float = 0.01) -> bool:
        """
        Check if option is at the money within a tolerance.
        
        Args:
            tolerance: Relative tolerance for ATM determination
            
        Returns:
            True if option is approximately at the money
        """
        return abs(self.moneyness - 1) <= tolerance
    
    def is_out_of_the_money(self) -> bool:
        """Check if option is out of the money."""
        if self.is_call:
            return self.underlying_price < self.strike_price
        return self.underlying_price > self.strike_price
    
    def copy_with(
        self,
        underlying_price: Optional[float] = None,
        strike_price: Optional[float] = None,
        time_to_expiry: Optional[float] = None,
        risk_free_rate: Optional[float] = None,
        volatility: Optional[float] = None,
        option_type: Optional[OptionType] = None,
        dividend_yield: Optional[float] = None
    ) -> "Option":
        """
        Create a copy of the option with modified parameters.
        
        Args:
            underlying_price: New underlying price (optional)
            strike_price: New strike price (optional)
            time_to_expiry: New time to expiry (optional)
            risk_free_rate: New risk-free rate (optional)
            volatility: New volatility (optional)
            option_type: New option type (optional)
            dividend_yield: New dividend yield (optional)
            
        Returns:
            New Option instance with updated parameters
        """
        return Option(
            underlying_price=underlying_price if underlying_price is not None else self.underlying_price,
            strike_price=strike_price if strike_price is not None else self.strike_price,
            time_to_expiry=time_to_expiry if time_to_expiry is not None else self.time_to_expiry,
            risk_free_rate=risk_free_rate if risk_free_rate is not None else self.risk_free_rate,
            volatility=volatility if volatility is not None else self.volatility,
            option_type=option_type if option_type is not None else self.option_type,
            dividend_yield=dividend_yield if dividend_yield is not None else self.dividend_yield
        )
    
    def __str__(self) -> str:
        """Return string representation of the option."""
        return (
            f"{self.option_type.value.upper()} Option: "
            f"S={self.underlying_price:.2f}, K={self.strike_price:.2f}, "
            f"T={self.time_to_expiry:.4f}y, σ={self.volatility:.2%}, "
            f"r={self.risk_free_rate:.2%}"
        )
