"""
Portfolio management for options trading.

This module provides portfolio tracking, risk management, and position management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .models.option import Option, OptionType
from .models.black_scholes import BlackScholes
from .models.greeks import Greeks, calculate_portfolio_greeks
from .strategies.strategy import Strategy


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """
    Represents a single position in the portfolio.
    
    Attributes:
        option: The option contract
        quantity: Number of contracts (always positive)
        side: Long or short position
        entry_price: Price at which position was opened
        entry_date: Date when position was opened
        contract_multiplier: Shares per contract (default 100)
    """
    option: Option
    quantity: int
    side: PositionSide
    entry_price: float
    entry_date: datetime = field(default_factory=datetime.now)
    contract_multiplier: int = 100
    
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.entry_price < 0:
            raise ValueError("Entry price cannot be negative")
    
    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.side == PositionSide.LONG
    
    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.side == PositionSide.SHORT
    
    @property
    def signed_quantity(self) -> int:
        """Return quantity with sign (positive for long, negative for short)."""
        return self.quantity if self.is_long else -self.quantity
    
    def current_price(self) -> float:
        """Calculate current theoretical price of the option."""
        return BlackScholes.price(self.option)
    
    def market_value(self) -> float:
        """
        Calculate current market value of the position.
        
        Returns:
            Positive for long positions, negative for short positions
        """
        return self.current_price() * self.signed_quantity * self.contract_multiplier
    
    def cost_basis(self) -> float:
        """
        Calculate the cost basis of the position.
        
        Returns:
            Total cost (positive) or credit (negative) to open position
        """
        return self.entry_price * self.signed_quantity * self.contract_multiplier
    
    def unrealized_pnl(self) -> float:
        """
        Calculate unrealized profit/loss.
        
        Returns:
            Unrealized P&L (positive for profit, negative for loss)
        """
        return self.market_value() - self.cost_basis()
    
    def unrealized_pnl_percent(self) -> float:
        """
        Calculate unrealized P&L as percentage of cost basis.
        
        Returns:
            P&L percentage (e.g., 0.10 for 10% profit)
        """
        basis = abs(self.cost_basis())
        if basis == 0:
            return 0.0
        return self.unrealized_pnl() / basis
    
    def greeks(self) -> Greeks:
        """Calculate position Greeks (scaled by signed quantity)."""
        base_greeks = Greeks.calculate(self.option)
        multiplier = self.signed_quantity * self.contract_multiplier
        return Greeks(
            delta=base_greeks.delta * multiplier,
            gamma=base_greeks.gamma * multiplier,
            theta=base_greeks.theta * multiplier,
            vega=base_greeks.vega * multiplier,
            rho=base_greeks.rho * multiplier
        )
    
    def __str__(self) -> str:
        """Return string representation of the position."""
        side_str = "Long" if self.is_long else "Short"
        return (
            f"{side_str} {self.quantity} x {self.option}\n"
            f"  Entry: ${self.entry_price:.2f}, Current: ${self.current_price():.2f}\n"
            f"  P&L: ${self.unrealized_pnl():.2f} ({self.unrealized_pnl_percent():.1%})"
        )


@dataclass
class Portfolio:
    """
    Options portfolio manager.
    
    Tracks positions, calculates aggregate metrics, and provides risk management.
    
    Attributes:
        name: Portfolio name
        cash_balance: Available cash balance
        positions: List of option positions
    """
    name: str = "Default Portfolio"
    cash_balance: float = 0.0
    positions: List[Position] = field(default_factory=list)
    
    def add_position(
        self,
        option: Option,
        quantity: int,
        side: PositionSide,
        entry_price: Optional[float] = None
    ) -> Position:
        """
        Add a new position to the portfolio.
        
        Args:
            option: Option contract
            quantity: Number of contracts
            side: Long or short
            entry_price: Entry price (if None, uses current theoretical price)
            
        Returns:
            The created Position object
        """
        if entry_price is None:
            entry_price = BlackScholes.price(option)
        
        position = Position(
            option=option,
            quantity=quantity,
            side=side,
            entry_price=entry_price
        )
        
        # Adjust cash balance
        cost = position.cost_basis()
        self.cash_balance -= cost
        
        self.positions.append(position)
        return position
    
    def close_position(self, position: Position, exit_price: Optional[float] = None) -> float:
        """
        Close an existing position.
        
        Args:
            position: Position to close
            exit_price: Exit price (if None, uses current theoretical price)
            
        Returns:
            Realized P&L from closing the position
        """
        if position not in self.positions:
            raise ValueError("Position not found in portfolio")
        
        if exit_price is None:
            exit_price = BlackScholes.price(position.option)
        
        # Calculate realized P&L
        exit_value = exit_price * position.signed_quantity * position.contract_multiplier
        realized_pnl = exit_value - position.cost_basis()
        
        # Adjust cash balance
        self.cash_balance += exit_value
        
        # Remove position
        self.positions.remove(position)
        
        return realized_pnl
    
    def total_market_value(self) -> float:
        """Calculate total market value of all positions."""
        return sum(pos.market_value() for pos in self.positions)
    
    def total_cost_basis(self) -> float:
        """Calculate total cost basis of all positions."""
        return sum(pos.cost_basis() for pos in self.positions)
    
    def total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L."""
        return sum(pos.unrealized_pnl() for pos in self.positions)
    
    def net_liquidation_value(self) -> float:
        """Calculate total portfolio value (cash + positions)."""
        return self.cash_balance + self.total_market_value()
    
    def portfolio_greeks(self) -> Greeks:
        """Calculate aggregate portfolio Greeks."""
        if not self.positions:
            return Greeks(0, 0, 0, 0, 0)
        
        total_delta = sum(pos.greeks().delta for pos in self.positions)
        total_gamma = sum(pos.greeks().gamma for pos in self.positions)
        total_theta = sum(pos.greeks().theta for pos in self.positions)
        total_vega = sum(pos.greeks().vega for pos in self.positions)
        total_rho = sum(pos.greeks().rho for pos in self.positions)
        
        return Greeks(
            delta=total_delta,
            gamma=total_gamma,
            theta=total_theta,
            vega=total_vega,
            rho=total_rho
        )
    
    def delta_exposure(self) -> float:
        """
        Calculate net delta exposure in dollar terms.
        
        Represents the equivalent stock position exposure.
        """
        return self.portfolio_greeks().delta
    
    def theta_decay(self) -> float:
        """
        Calculate expected daily theta decay.
        
        Returns:
            Expected daily P&L change from time decay
        """
        return self.portfolio_greeks().theta / 365
    
    def vega_exposure(self) -> float:
        """
        Calculate vega exposure.
        
        Returns:
            Expected P&L change per 1% change in volatility
        """
        return self.portfolio_greeks().vega
    
    def positions_by_underlying(self) -> Dict[float, List[Position]]:
        """Group positions by underlying price (assuming same underlying)."""
        groups: Dict[float, List[Position]] = {}
        for pos in self.positions:
            price = pos.option.underlying_price
            if price not in groups:
                groups[price] = []
            groups[price].append(pos)
        return groups
    
    def positions_by_expiry(self) -> Dict[float, List[Position]]:
        """Group positions by time to expiry."""
        groups: Dict[float, List[Position]] = {}
        for pos in self.positions:
            expiry = pos.option.time_to_expiry
            if expiry not in groups:
                groups[expiry] = []
            groups[expiry].append(pos)
        return groups
    
    def expiring_soon(self, days: float = 7) -> List[Position]:
        """
        Get positions expiring within specified days.
        
        Args:
            days: Number of days threshold
            
        Returns:
            List of positions expiring within the threshold
        """
        threshold = days / 365
        return [
            pos for pos in self.positions
            if pos.option.time_to_expiry <= threshold
        ]
    
    def risk_summary(self) -> Dict:
        """
        Generate a risk summary for the portfolio.
        
        Returns:
            Dictionary with risk metrics
        """
        greeks = self.portfolio_greeks()
        
        return {
            "net_liquidation_value": self.net_liquidation_value(),
            "cash_balance": self.cash_balance,
            "total_market_value": self.total_market_value(),
            "unrealized_pnl": self.total_unrealized_pnl(),
            "position_count": len(self.positions),
            "delta_exposure": greeks.delta,
            "gamma": greeks.gamma,
            "theta_daily": greeks.theta / 365,
            "vega": greeks.vega,
            "rho": greeks.rho,
            "expiring_7_days": len(self.expiring_soon(7)),
        }
    
    def __str__(self) -> str:
        """Return string representation of the portfolio."""
        lines = [
            f"Portfolio: {self.name}",
            f"{'=' * 50}",
            f"Cash Balance: ${self.cash_balance:,.2f}",
            f"Market Value: ${self.total_market_value():,.2f}",
            f"Net Liquidation: ${self.net_liquidation_value():,.2f}",
            f"Unrealized P&L: ${self.total_unrealized_pnl():,.2f}",
            f"",
            f"Positions ({len(self.positions)}):",
            f"{'-' * 50}"
        ]
        
        for i, pos in enumerate(self.positions, 1):
            lines.append(f"{i}. {pos}")
            lines.append("")
        
        if self.positions:
            lines.append(f"Portfolio Greeks:")
            lines.append(str(self.portfolio_greeks()))
        
        return "\n".join(lines)
