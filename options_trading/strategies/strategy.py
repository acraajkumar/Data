"""
Trading strategies for options.

This module implements common options trading strategies including:
- Single leg strategies (Long Call, Long Put, etc.)
- Spreads (Bull Call Spread, Bear Put Spread, etc.)
- Straddles and Strangles
- Iron Condor and Iron Butterfly
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional

from ..models.option import Option, OptionType
from ..models.black_scholes import BlackScholes
from ..models.greeks import Greeks, calculate_portfolio_greeks


class StrategyType(Enum):
    """Common options strategy types."""
    LONG_CALL = "long_call"
    SHORT_CALL = "short_call"
    LONG_PUT = "long_put"
    SHORT_PUT = "short_put"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    BULL_PUT_SPREAD = "bull_put_spread"
    BEAR_CALL_SPREAD = "bear_call_spread"
    LONG_STRADDLE = "long_straddle"
    SHORT_STRADDLE = "short_straddle"
    LONG_STRANGLE = "long_strangle"
    SHORT_STRANGLE = "short_strangle"
    IRON_CONDOR = "iron_condor"
    IRON_BUTTERFLY = "iron_butterfly"
    CUSTOM = "custom"


@dataclass
class StrategyLeg:
    """
    Represents a single leg of an options strategy.
    
    Attributes:
        option: The option contract
        quantity: Number of contracts (positive for long, negative for short)
    """
    option: Option
    quantity: int
    
    @property
    def is_long(self) -> bool:
        """Check if this is a long position."""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if this is a short position."""
        return self.quantity < 0
    
    def value(self) -> float:
        """Calculate the current value of this leg."""
        return BlackScholes.price(self.option) * abs(self.quantity)
    
    def cost(self) -> float:
        """
        Calculate the cost/credit for opening this position.
        
        Returns:
            Positive for debit (cost), negative for credit
        """
        price = BlackScholes.price(self.option)
        return price * self.quantity
    
    def greeks(self) -> Greeks:
        """Calculate Greeks for this leg (scaled by quantity)."""
        base_greeks = Greeks.calculate(self.option)
        return Greeks(
            delta=base_greeks.delta * self.quantity,
            gamma=base_greeks.gamma * self.quantity,
            theta=base_greeks.theta * self.quantity,
            vega=base_greeks.vega * self.quantity,
            rho=base_greeks.rho * self.quantity
        )


@dataclass
class Strategy:
    """
    Represents a complete options trading strategy.
    
    Attributes:
        name: Name of the strategy
        strategy_type: Type of strategy
        legs: List of strategy legs
        underlying_position: Number of underlying shares (for covered strategies)
    """
    name: str
    strategy_type: StrategyType
    legs: List[StrategyLeg] = field(default_factory=list)
    underlying_position: int = 0
    underlying_price: float = 0.0
    
    def add_leg(self, option: Option, quantity: int) -> None:
        """
        Add a leg to the strategy.
        
        Args:
            option: Option contract to add
            quantity: Number of contracts (positive for long, negative for short)
        """
        self.legs.append(StrategyLeg(option, quantity))
    
    def total_cost(self) -> float:
        """
        Calculate total cost/credit for the strategy.
        
        Returns:
            Net cost (positive) or credit (negative) for opening the position
        """
        return sum(leg.cost() for leg in self.legs)
    
    def max_profit(self, price_range: Tuple[float, float] = (0, float('inf'))) -> float:
        """
        Estimate maximum profit within a price range.
        
        Args:
            price_range: Tuple of (min_price, max_price) for underlying
            
        Returns:
            Estimated maximum profit
        """
        return self._calculate_payoff_at_expiry(price_range, find_max=True)
    
    def max_loss(self, price_range: Tuple[float, float] = (0, float('inf'))) -> float:
        """
        Estimate maximum loss within a price range.
        
        Args:
            price_range: Tuple of (min_price, max_price) for underlying
            
        Returns:
            Estimated maximum loss (as positive number)
        """
        return -self._calculate_payoff_at_expiry(price_range, find_max=False)
    
    def _calculate_payoff_at_expiry(
        self,
        price_range: Tuple[float, float],
        find_max: bool,
        num_points: int = 1000
    ) -> float:
        """Calculate payoff at expiration."""
        min_price, max_price = price_range
        if max_price == float('inf'):
            # Use a reasonable upper bound
            max_strike = max(leg.option.strike_price for leg in self.legs)
            max_price = max_strike * 3
        
        step = (max_price - min_price) / num_points
        initial_cost = self.total_cost()
        
        extreme_payoff = float('-inf') if find_max else float('inf')
        
        for i in range(num_points + 1):
            price = min_price + i * step
            payoff = self._payoff_at_price(price) - initial_cost
            
            if find_max:
                extreme_payoff = max(extreme_payoff, payoff)
            else:
                extreme_payoff = min(extreme_payoff, payoff)
        
        # Add underlying position P&L if any
        if self.underlying_position != 0:
            # This is a simplification; would need initial underlying price
            pass
        
        return extreme_payoff
    
    def _payoff_at_price(self, underlying_price: float) -> float:
        """Calculate total payoff at a given underlying price at expiration."""
        total = 0.0
        
        for leg in self.legs:
            option = leg.option
            if option.is_call:
                intrinsic = max(0, underlying_price - option.strike_price)
            else:
                intrinsic = max(0, option.strike_price - underlying_price)
            
            total += intrinsic * leg.quantity
        
        return total
    
    def breakeven_points(self, tolerance: float = 0.01) -> List[float]:
        """
        Calculate breakeven points at expiration.
        
        Args:
            tolerance: Acceptable error for breakeven calculation
            
        Returns:
            List of underlying prices where P&L = 0
        """
        if not self.legs:
            return []
        
        initial_cost = self.total_cost()
        
        # Get all strike prices and add boundary points
        strikes = sorted(set(leg.option.strike_price for leg in self.legs))
        min_strike = min(strikes)
        max_strike = max(strikes)
        
        # Extend range beyond strikes
        test_prices = [min_strike * 0.5]
        test_prices.extend(strikes)
        test_prices.append(max_strike * 1.5)
        
        breakevens = []
        
        # Find sign changes between test points
        for i in range(len(test_prices) - 1):
            p1 = test_prices[i]
            p2 = test_prices[i + 1]
            
            pnl1 = self._payoff_at_price(p1) - initial_cost
            pnl2 = self._payoff_at_price(p2) - initial_cost
            
            # Check for sign change
            if pnl1 * pnl2 < 0:
                # Binary search for exact breakeven
                low, high = p1, p2
                while high - low > tolerance:
                    mid = (low + high) / 2
                    pnl_mid = self._payoff_at_price(mid) - initial_cost
                    
                    if pnl_mid * pnl1 < 0:
                        high = mid
                    else:
                        low = mid
                
                breakevens.append((low + high) / 2)
        
        return breakevens
    
    def portfolio_greeks(self) -> Greeks:
        """Calculate aggregate Greeks for the entire strategy."""
        positions = [(leg.option, leg.quantity) for leg in self.legs]
        return calculate_portfolio_greeks(positions)
    
    def profit_probability(
        self,
        volatility: float,
        days_to_expiry: float,
        num_simulations: int = 10000
    ) -> float:
        """
        Estimate probability of profit using Monte Carlo simulation.
        
        Args:
            volatility: Expected volatility (annualized)
            days_to_expiry: Days until expiration
            num_simulations: Number of Monte Carlo paths
            
        Returns:
            Estimated probability of profit
        """
        import random
        import math
        
        if not self.legs:
            return 0.0
        
        current_price = self.legs[0].option.underlying_price
        time_years = days_to_expiry / 365
        
        if time_years <= 0:
            return 0.0
        
        initial_cost = self.total_cost()
        profitable_count = 0
        
        for _ in range(num_simulations):
            # Simulate log-normal price movement
            z = random.gauss(0, 1)
            drift = -0.5 * volatility ** 2 * time_years
            diffusion = volatility * math.sqrt(time_years) * z
            final_price = current_price * math.exp(drift + diffusion)
            
            payoff = self._payoff_at_price(final_price) - initial_cost
            if payoff > 0:
                profitable_count += 1
        
        return profitable_count / num_simulations
    
    def __str__(self) -> str:
        """Return string representation of the strategy."""
        lines = [f"Strategy: {self.name} ({self.strategy_type.value})"]
        lines.append(f"Net Cost/Credit: ${self.total_cost():.2f}")
        lines.append("Legs:")
        
        for i, leg in enumerate(self.legs, 1):
            direction = "Long" if leg.is_long else "Short"
            lines.append(
                f"  {i}. {direction} {abs(leg.quantity)} x {leg.option}"
            )
        
        greeks = self.portfolio_greeks()
        lines.append(f"\n{greeks}")
        
        return "\n".join(lines)


# Factory functions for common strategies

def create_long_call(
    underlying_price: float,
    strike_price: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    quantity: int = 1
) -> Strategy:
    """Create a long call strategy."""
    option = Option(
        underlying_price=underlying_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.CALL
    )
    
    strategy = Strategy("Long Call", StrategyType.LONG_CALL)
    strategy.add_leg(option, quantity)
    return strategy


def create_long_put(
    underlying_price: float,
    strike_price: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    quantity: int = 1
) -> Strategy:
    """Create a long put strategy."""
    option = Option(
        underlying_price=underlying_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.PUT
    )
    
    strategy = Strategy("Long Put", StrategyType.LONG_PUT)
    strategy.add_leg(option, quantity)
    return strategy


def create_bull_call_spread(
    underlying_price: float,
    lower_strike: float,
    upper_strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    quantity: int = 1
) -> Strategy:
    """Create a bull call spread (buy lower strike call, sell higher strike call)."""
    long_call = Option(
        underlying_price=underlying_price,
        strike_price=lower_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.CALL
    )
    
    short_call = Option(
        underlying_price=underlying_price,
        strike_price=upper_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.CALL
    )
    
    strategy = Strategy("Bull Call Spread", StrategyType.BULL_CALL_SPREAD)
    strategy.add_leg(long_call, quantity)
    strategy.add_leg(short_call, -quantity)
    return strategy


def create_bear_put_spread(
    underlying_price: float,
    lower_strike: float,
    upper_strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    quantity: int = 1
) -> Strategy:
    """Create a bear put spread (buy higher strike put, sell lower strike put)."""
    long_put = Option(
        underlying_price=underlying_price,
        strike_price=upper_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.PUT
    )
    
    short_put = Option(
        underlying_price=underlying_price,
        strike_price=lower_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.PUT
    )
    
    strategy = Strategy("Bear Put Spread", StrategyType.BEAR_PUT_SPREAD)
    strategy.add_leg(long_put, quantity)
    strategy.add_leg(short_put, -quantity)
    return strategy


def create_long_straddle(
    underlying_price: float,
    strike_price: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    quantity: int = 1
) -> Strategy:
    """Create a long straddle (buy call and put at same strike)."""
    call = Option(
        underlying_price=underlying_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.CALL
    )
    
    put = Option(
        underlying_price=underlying_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.PUT
    )
    
    strategy = Strategy("Long Straddle", StrategyType.LONG_STRADDLE)
    strategy.add_leg(call, quantity)
    strategy.add_leg(put, quantity)
    return strategy


def create_iron_condor(
    underlying_price: float,
    put_lower_strike: float,
    put_upper_strike: float,
    call_lower_strike: float,
    call_upper_strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    quantity: int = 1
) -> Strategy:
    """
    Create an iron condor strategy.
    
    Structure:
    - Buy OTM put (put_lower_strike)
    - Sell OTM put (put_upper_strike)
    - Sell OTM call (call_lower_strike)
    - Buy OTM call (call_upper_strike)
    """
    long_put = Option(
        underlying_price=underlying_price,
        strike_price=put_lower_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.PUT
    )
    
    short_put = Option(
        underlying_price=underlying_price,
        strike_price=put_upper_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.PUT
    )
    
    short_call = Option(
        underlying_price=underlying_price,
        strike_price=call_lower_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.CALL
    )
    
    long_call = Option(
        underlying_price=underlying_price,
        strike_price=call_upper_strike,
        time_to_expiry=time_to_expiry,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        option_type=OptionType.CALL
    )
    
    strategy = Strategy("Iron Condor", StrategyType.IRON_CONDOR)
    strategy.add_leg(long_put, quantity)
    strategy.add_leg(short_put, -quantity)
    strategy.add_leg(short_call, -quantity)
    strategy.add_leg(long_call, quantity)
    return strategy
