"""
Black-Scholes Option Pricing Model.

This module implements the Black-Scholes-Merton model for pricing European options.
"""

import math
from typing import Tuple

from .option import Option, OptionType


class BlackScholes:
    """
    Black-Scholes-Merton option pricing model.
    
    Implements the analytical solution for pricing European call and put options
    on non-dividend paying stocks, with support for continuous dividend yields.
    """
    
    @staticmethod
    def _standard_normal_cdf(x: float) -> float:
        """
        Calculate the cumulative distribution function for standard normal distribution.
        
        Uses the error function for accurate calculation.
        
        Args:
            x: Value to evaluate CDF at
            
        Returns:
            P(X <= x) where X ~ N(0, 1)
        """
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def _standard_normal_pdf(x: float) -> float:
        """
        Calculate the probability density function for standard normal distribution.
        
        Args:
            x: Value to evaluate PDF at
            
        Returns:
            PDF value at x for N(0, 1)
        """
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    @classmethod
    def _calculate_d1_d2(cls, option: Option) -> Tuple[float, float]:
        """
        Calculate d1 and d2 parameters used in Black-Scholes formula.
        
        Args:
            option: Option contract parameters
            
        Returns:
            Tuple of (d1, d2) values
        """
        if option.time_to_expiry == 0:
            # At expiration, return extreme values
            if option.underlying_price > option.strike_price:
                return float('inf'), float('inf')
            elif option.underlying_price < option.strike_price:
                return float('-inf'), float('-inf')
            else:
                return 0, 0
        
        if option.volatility == 0:
            # Zero volatility case
            forward = option.underlying_price * math.exp(
                (option.risk_free_rate - option.dividend_yield) * option.time_to_expiry
            )
            pv_strike = option.strike_price * math.exp(-option.risk_free_rate * option.time_to_expiry)
            if forward > pv_strike:
                return float('inf'), float('inf')
            elif forward < pv_strike:
                return float('-inf'), float('-inf')
            else:
                return 0, 0
        
        sqrt_t = math.sqrt(option.time_to_expiry)
        
        d1 = (
            math.log(option.underlying_price / option.strike_price) +
            (option.risk_free_rate - option.dividend_yield + 0.5 * option.volatility ** 2) * option.time_to_expiry
        ) / (option.volatility * sqrt_t)
        
        d2 = d1 - option.volatility * sqrt_t
        
        return d1, d2
    
    @classmethod
    def price(cls, option: Option) -> float:
        """
        Calculate the theoretical price of a European option.
        
        Args:
            option: Option contract to price
            
        Returns:
            Theoretical option price
        """
        if option.time_to_expiry == 0:
            return option.intrinsic_value
        
        d1, d2 = cls._calculate_d1_d2(option)
        
        S = option.underlying_price
        K = option.strike_price
        T = option.time_to_expiry
        r = option.risk_free_rate
        q = option.dividend_yield
        
        discount_factor = math.exp(-r * T)
        forward_factor = math.exp(-q * T)
        
        if option.is_call:
            price = (
                S * forward_factor * cls._standard_normal_cdf(d1) -
                K * discount_factor * cls._standard_normal_cdf(d2)
            )
        else:
            price = (
                K * discount_factor * cls._standard_normal_cdf(-d2) -
                S * forward_factor * cls._standard_normal_cdf(-d1)
            )
        
        return max(0, price)
    
    @classmethod
    def delta(cls, option: Option) -> float:
        """
        Calculate Delta - rate of change of option price with respect to underlying price.
        
        Args:
            option: Option contract
            
        Returns:
            Delta value (between -1 and 1)
        """
        if option.time_to_expiry == 0:
            if option.is_call:
                return 1.0 if option.underlying_price > option.strike_price else 0.0
            else:
                return -1.0 if option.underlying_price < option.strike_price else 0.0
        
        d1, _ = cls._calculate_d1_d2(option)
        forward_factor = math.exp(-option.dividend_yield * option.time_to_expiry)
        
        if option.is_call:
            return forward_factor * cls._standard_normal_cdf(d1)
        else:
            return forward_factor * (cls._standard_normal_cdf(d1) - 1)
    
    @classmethod
    def gamma(cls, option: Option) -> float:
        """
        Calculate Gamma - rate of change of Delta with respect to underlying price.
        
        Args:
            option: Option contract
            
        Returns:
            Gamma value (always non-negative)
        """
        if option.time_to_expiry == 0 or option.volatility == 0:
            return 0.0
        
        d1, _ = cls._calculate_d1_d2(option)
        forward_factor = math.exp(-option.dividend_yield * option.time_to_expiry)
        
        return (
            forward_factor * cls._standard_normal_pdf(d1) /
            (option.underlying_price * option.volatility * math.sqrt(option.time_to_expiry))
        )
    
    @classmethod
    def theta(cls, option: Option) -> float:
        """
        Calculate Theta - rate of change of option price with respect to time.
        
        Args:
            option: Option contract
            
        Returns:
            Theta value (typically negative, expressed per year)
        """
        if option.time_to_expiry == 0:
            return 0.0
        
        d1, d2 = cls._calculate_d1_d2(option)
        
        S = option.underlying_price
        K = option.strike_price
        T = option.time_to_expiry
        r = option.risk_free_rate
        q = option.dividend_yield
        sigma = option.volatility
        
        sqrt_t = math.sqrt(T)
        forward_factor = math.exp(-q * T)
        discount_factor = math.exp(-r * T)
        
        # Common term
        common = (
            -S * forward_factor * cls._standard_normal_pdf(d1) * sigma /
            (2 * sqrt_t)
        )
        
        if option.is_call:
            theta = (
                common -
                r * K * discount_factor * cls._standard_normal_cdf(d2) +
                q * S * forward_factor * cls._standard_normal_cdf(d1)
            )
        else:
            theta = (
                common +
                r * K * discount_factor * cls._standard_normal_cdf(-d2) -
                q * S * forward_factor * cls._standard_normal_cdf(-d1)
            )
        
        return theta
    
    @classmethod
    def vega(cls, option: Option) -> float:
        """
        Calculate Vega - rate of change of option price with respect to volatility.
        
        Args:
            option: Option contract
            
        Returns:
            Vega value (expressed per 1% change in volatility)
        """
        if option.time_to_expiry == 0:
            return 0.0
        
        d1, _ = cls._calculate_d1_d2(option)
        forward_factor = math.exp(-option.dividend_yield * option.time_to_expiry)
        sqrt_t = math.sqrt(option.time_to_expiry)
        
        # Vega is the same for calls and puts
        vega = (
            option.underlying_price * forward_factor *
            cls._standard_normal_pdf(d1) * sqrt_t
        )
        
        # Return as per 1% change (multiply by 0.01)
        return vega * 0.01
    
    @classmethod
    def rho(cls, option: Option) -> float:
        """
        Calculate Rho - rate of change of option price with respect to interest rate.
        
        Args:
            option: Option contract
            
        Returns:
            Rho value (expressed per 1% change in interest rate)
        """
        if option.time_to_expiry == 0:
            return 0.0
        
        _, d2 = cls._calculate_d1_d2(option)
        
        K = option.strike_price
        T = option.time_to_expiry
        r = option.risk_free_rate
        
        discount_factor = math.exp(-r * T)
        
        if option.is_call:
            rho = K * T * discount_factor * cls._standard_normal_cdf(d2)
        else:
            rho = -K * T * discount_factor * cls._standard_normal_cdf(-d2)
        
        # Return as per 1% change (multiply by 0.01)
        return rho * 0.01
    
    @classmethod
    def implied_volatility(
        cls,
        option: Option,
        market_price: float,
        max_iterations: int = 100,
        tolerance: float = 1e-8
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Args:
            option: Option contract (volatility parameter will be ignored)
            market_price: Observed market price of the option
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Implied volatility as a decimal
            
        Raises:
            ValueError: If implied volatility cannot be found
        """
        if market_price <= 0:
            raise ValueError("Market price must be positive")
        
        # Check bounds
        intrinsic = option.intrinsic_value
        if market_price < intrinsic:
            raise ValueError(
                f"Market price {market_price} is below intrinsic value {intrinsic}"
            )
        
        # Initial guess using Brenner-Subrahmanyam approximation
        sigma = math.sqrt(2 * math.pi / option.time_to_expiry) * market_price / option.underlying_price
        sigma = max(0.001, min(sigma, 5.0))  # Bound initial guess
        
        for _ in range(max_iterations):
            test_option = option.copy_with(volatility=sigma)
            price = cls.price(test_option)
            vega = cls.vega(test_option) / 0.01  # Convert back to raw vega
            
            price_diff = price - market_price
            
            if abs(price_diff) < tolerance:
                return sigma
            
            if abs(vega) < 1e-10:
                # Vega too small, use bisection fallback
                break
            
            sigma -= price_diff / vega
            sigma = max(0.001, min(sigma, 5.0))  # Keep sigma in reasonable bounds
        
        # Fallback to bisection method
        low, high = 0.001, 5.0
        for _ in range(max_iterations):
            mid = (low + high) / 2
            test_option = option.copy_with(volatility=mid)
            price = cls.price(test_option)
            
            if abs(price - market_price) < tolerance:
                return mid
            
            if price < market_price:
                low = mid
            else:
                high = mid
        
        raise ValueError(
            f"Could not find implied volatility within {max_iterations} iterations"
        )
