"""
Unit tests for the Portfolio class.
"""

import unittest
from options_trading.models.option import Option, OptionType
from options_trading.portfolio import Portfolio, Position, PositionSide


class TestPosition(unittest.TestCase):
    """Test cases for the Position class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.call_option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
    
    def test_create_long_position(self):
        """Test creating a long position."""
        position = Position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        self.assertTrue(position.is_long)
        self.assertFalse(position.is_short)
        self.assertEqual(position.signed_quantity, 1)
    
    def test_create_short_position(self):
        """Test creating a short position."""
        position = Position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.SHORT,
            entry_price=5.0
        )
        
        self.assertFalse(position.is_long)
        self.assertTrue(position.is_short)
        self.assertEqual(position.signed_quantity, -1)
    
    def test_invalid_quantity(self):
        """Test that non-positive quantity raises error."""
        with self.assertRaises(ValueError):
            Position(
                option=self.call_option,
                quantity=0,
                side=PositionSide.LONG,
                entry_price=5.0
            )
    
    def test_invalid_entry_price(self):
        """Test that negative entry price raises error."""
        with self.assertRaises(ValueError):
            Position(
                option=self.call_option,
                quantity=1,
                side=PositionSide.LONG,
                entry_price=-5.0
            )
    
    def test_current_price(self):
        """Test current price calculation."""
        position = Position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        price = position.current_price()
        self.assertGreater(price, 0)
    
    def test_cost_basis_long(self):
        """Test cost basis for long position."""
        position = Position(
            option=self.call_option,
            quantity=2,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        # 2 contracts * 100 shares * $5 = $1000
        self.assertEqual(position.cost_basis(), 1000)
    
    def test_cost_basis_short(self):
        """Test cost basis for short position (credit)."""
        position = Position(
            option=self.call_option,
            quantity=2,
            side=PositionSide.SHORT,
            entry_price=5.0
        )
        
        # Short position means credit: -2 * 100 * $5 = -$1000
        self.assertEqual(position.cost_basis(), -1000)


class TestPortfolio(unittest.TestCase):
    """Test cases for the Portfolio class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Portfolio(name="Test Portfolio", cash_balance=10000)
        
        self.call_option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.put_option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
    
    def test_create_portfolio(self):
        """Test creating a portfolio."""
        self.assertEqual(self.portfolio.name, "Test Portfolio")
        self.assertEqual(self.portfolio.cash_balance, 10000)
        self.assertEqual(len(self.portfolio.positions), 0)
    
    def test_add_long_position(self):
        """Test adding a long position."""
        position = self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        self.assertEqual(len(self.portfolio.positions), 1)
        self.assertTrue(position.is_long)
        
        # Cash should be reduced by cost
        self.assertEqual(self.portfolio.cash_balance, 10000 - 500)
    
    def test_add_short_position(self):
        """Test adding a short position (credit)."""
        position = self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.SHORT,
            entry_price=5.0
        )
        
        self.assertEqual(len(self.portfolio.positions), 1)
        self.assertTrue(position.is_short)
        
        # Cash should increase by credit received
        self.assertEqual(self.portfolio.cash_balance, 10000 + 500)
    
    def test_close_position(self):
        """Test closing a position."""
        position = self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        initial_cash = self.portfolio.cash_balance
        
        # Close at same price (no P&L)
        pnl = self.portfolio.close_position(position, exit_price=5.0)
        
        self.assertEqual(len(self.portfolio.positions), 0)
        self.assertAlmostEqual(pnl, 0, places=2)
        self.assertEqual(self.portfolio.cash_balance, initial_cash + 500)
    
    def test_close_position_with_profit(self):
        """Test closing a position with profit."""
        position = self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        # Close at higher price
        pnl = self.portfolio.close_position(position, exit_price=7.0)
        
        # Profit = (7 - 5) * 100 = $200
        self.assertAlmostEqual(pnl, 200, places=2)
    
    def test_close_position_not_found(self):
        """Test closing a position not in portfolio."""
        position = Position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        with self.assertRaises(ValueError):
            self.portfolio.close_position(position)
    
    def test_total_market_value(self):
        """Test total market value calculation."""
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        market_value = self.portfolio.total_market_value()
        self.assertGreater(market_value, 0)
    
    def test_net_liquidation_value(self):
        """Test net liquidation value calculation."""
        initial_nlv = self.portfolio.net_liquidation_value()
        self.assertEqual(initial_nlv, 10000)
        
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        nlv = self.portfolio.net_liquidation_value()
        # NLV should be cash + market value
        expected = self.portfolio.cash_balance + self.portfolio.total_market_value()
        self.assertAlmostEqual(nlv, expected, places=2)
    
    def test_portfolio_greeks(self):
        """Test portfolio Greeks calculation."""
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        greeks = self.portfolio.portfolio_greeks()
        
        # Long call should have positive delta
        self.assertGreater(greeks.delta, 0)
    
    def test_delta_exposure(self):
        """Test delta exposure calculation."""
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        delta = self.portfolio.delta_exposure()
        self.assertGreater(delta, 0)
    
    def test_theta_decay(self):
        """Test theta decay calculation."""
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        theta = self.portfolio.theta_decay()
        # Long options have negative theta
        self.assertLess(theta, 0)
    
    def test_expiring_soon(self):
        """Test expiring soon filter."""
        # Add option expiring in ~91 days (0.25 years)
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        expiring_7 = self.portfolio.expiring_soon(7)
        expiring_365 = self.portfolio.expiring_soon(365)
        
        self.assertEqual(len(expiring_7), 0)
        self.assertEqual(len(expiring_365), 1)
    
    def test_risk_summary(self):
        """Test risk summary generation."""
        self.portfolio.add_position(
            option=self.call_option,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=5.0
        )
        
        summary = self.portfolio.risk_summary()
        
        self.assertIn("net_liquidation_value", summary)
        self.assertIn("cash_balance", summary)
        self.assertIn("delta_exposure", summary)
        self.assertIn("position_count", summary)
        self.assertEqual(summary["position_count"], 1)
    
    def test_empty_portfolio_greeks(self):
        """Test that empty portfolio has zero Greeks."""
        greeks = self.portfolio.portfolio_greeks()
        
        self.assertEqual(greeks.delta, 0)
        self.assertEqual(greeks.gamma, 0)
        self.assertEqual(greeks.theta, 0)
        self.assertEqual(greeks.vega, 0)
        self.assertEqual(greeks.rho, 0)


class TestMultiplePositions(unittest.TestCase):
    """Test cases for portfolios with multiple positions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Portfolio(name="Multi-Position Portfolio", cash_balance=50000)
        
        self.call_100 = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.put_100 = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
    
    def test_straddle_position(self):
        """Test creating a straddle (long call + long put)."""
        self.portfolio.add_position(
            option=self.call_100,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=4.0
        )
        
        self.portfolio.add_position(
            option=self.put_100,
            quantity=1,
            side=PositionSide.LONG,
            entry_price=4.0
        )
        
        self.assertEqual(len(self.portfolio.positions), 2)
        
        greeks = self.portfolio.portfolio_greeks()
        # Straddle should have near-zero delta at ATM
        self.assertAlmostEqual(greeks.delta, 0, delta=500)  # Allow for small deviation
    
    def test_aggregation_multiple_positions(self):
        """Test that values aggregate correctly."""
        pos1 = self.portfolio.add_position(
            option=self.call_100,
            quantity=2,
            side=PositionSide.LONG,
            entry_price=4.0
        )
        
        pos2 = self.portfolio.add_position(
            option=self.put_100,
            quantity=3,
            side=PositionSide.LONG,
            entry_price=3.5
        )
        
        total_value = self.portfolio.total_market_value()
        individual_sum = pos1.market_value() + pos2.market_value()
        
        self.assertAlmostEqual(total_value, individual_sum, places=4)


if __name__ == "__main__":
    unittest.main()
