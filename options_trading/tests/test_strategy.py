"""
Unit tests for trading strategies.
"""

import unittest
from options_trading.models.option import Option, OptionType
from options_trading.strategies.strategy import (
    Strategy,
    StrategyType,
    StrategyLeg,
    create_long_call,
    create_long_put,
    create_bull_call_spread,
    create_bear_put_spread,
    create_long_straddle,
    create_iron_condor
)


class TestStrategyLeg(unittest.TestCase):
    """Test cases for StrategyLeg."""
    
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
    
    def test_long_leg(self):
        """Test creating a long leg."""
        leg = StrategyLeg(self.call_option, 1)
        
        self.assertTrue(leg.is_long)
        self.assertFalse(leg.is_short)
    
    def test_short_leg(self):
        """Test creating a short leg."""
        leg = StrategyLeg(self.call_option, -1)
        
        self.assertFalse(leg.is_long)
        self.assertTrue(leg.is_short)
    
    def test_leg_value_positive(self):
        """Test that leg value is positive."""
        leg = StrategyLeg(self.call_option, 1)
        
        self.assertGreater(leg.value(), 0)
    
    def test_long_leg_cost_positive(self):
        """Test that long leg cost is positive (debit)."""
        leg = StrategyLeg(self.call_option, 1)
        
        self.assertGreater(leg.cost(), 0)
    
    def test_short_leg_cost_negative(self):
        """Test that short leg cost is negative (credit)."""
        leg = StrategyLeg(self.call_option, -1)
        
        self.assertLess(leg.cost(), 0)


class TestStrategy(unittest.TestCase):
    """Test cases for Strategy class."""
    
    def test_create_strategy(self):
        """Test creating a basic strategy."""
        strategy = Strategy("Test Strategy", StrategyType.CUSTOM)
        
        self.assertEqual(strategy.name, "Test Strategy")
        self.assertEqual(strategy.strategy_type, StrategyType.CUSTOM)
        self.assertEqual(len(strategy.legs), 0)
    
    def test_add_leg(self):
        """Test adding legs to strategy."""
        strategy = Strategy("Test", StrategyType.CUSTOM)
        
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        strategy.add_leg(option, 1)
        
        self.assertEqual(len(strategy.legs), 1)
    
    def test_total_cost(self):
        """Test total cost calculation."""
        strategy = create_long_call(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
        
        cost = strategy.total_cost()
        self.assertGreater(cost, 0)


class TestLongCall(unittest.TestCase):
    """Test cases for long call strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = create_long_call(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
    
    def test_strategy_type(self):
        """Test strategy type is correct."""
        self.assertEqual(self.strategy.strategy_type, StrategyType.LONG_CALL)
    
    def test_single_leg(self):
        """Test strategy has single leg."""
        self.assertEqual(len(self.strategy.legs), 1)
    
    def test_leg_is_long(self):
        """Test the leg is a long position."""
        self.assertTrue(self.strategy.legs[0].is_long)
    
    def test_cost_is_debit(self):
        """Test that opening requires a debit."""
        self.assertGreater(self.strategy.total_cost(), 0)
    
    def test_max_loss_is_premium(self):
        """Test max loss equals premium paid."""
        max_loss = self.strategy.max_loss()
        cost = self.strategy.total_cost()
        
        self.assertAlmostEqual(max_loss, cost, places=2)
    
    def test_breakeven_above_strike(self):
        """Test breakeven is above strike price."""
        breakevens = self.strategy.breakeven_points()
        
        self.assertEqual(len(breakevens), 1)
        self.assertGreater(breakevens[0], 100)


class TestLongPut(unittest.TestCase):
    """Test cases for long put strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = create_long_put(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
    
    def test_strategy_type(self):
        """Test strategy type is correct."""
        self.assertEqual(self.strategy.strategy_type, StrategyType.LONG_PUT)
    
    def test_breakeven_below_strike(self):
        """Test breakeven is below strike price."""
        breakevens = self.strategy.breakeven_points()
        
        self.assertEqual(len(breakevens), 1)
        self.assertLess(breakevens[0], 100)


class TestBullCallSpread(unittest.TestCase):
    """Test cases for bull call spread strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = create_bull_call_spread(
            underlying_price=100,
            lower_strike=95,
            upper_strike=105,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
    
    def test_strategy_type(self):
        """Test strategy type is correct."""
        self.assertEqual(self.strategy.strategy_type, StrategyType.BULL_CALL_SPREAD)
    
    def test_two_legs(self):
        """Test strategy has two legs."""
        self.assertEqual(len(self.strategy.legs), 2)
    
    def test_one_long_one_short(self):
        """Test one long leg and one short leg."""
        long_legs = [leg for leg in self.strategy.legs if leg.is_long]
        short_legs = [leg for leg in self.strategy.legs if leg.is_short]
        
        self.assertEqual(len(long_legs), 1)
        self.assertEqual(len(short_legs), 1)
    
    def test_net_debit(self):
        """Test that spread is a net debit."""
        # Bull call spread should be a debit
        self.assertGreater(self.strategy.total_cost(), 0)
    
    def test_max_profit_limited(self):
        """Test max profit is limited."""
        max_profit = self.strategy.max_profit()
        
        # Max profit should be spread width minus premium
        spread_width = 105 - 95
        self.assertLess(max_profit, spread_width)
    
    def test_max_loss_limited(self):
        """Test max loss is limited to premium."""
        max_loss = self.strategy.max_loss()
        cost = self.strategy.total_cost()
        
        self.assertAlmostEqual(max_loss, cost, places=2)


class TestBearPutSpread(unittest.TestCase):
    """Test cases for bear put spread strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = create_bear_put_spread(
            underlying_price=100,
            lower_strike=95,
            upper_strike=105,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
    
    def test_strategy_type(self):
        """Test strategy type is correct."""
        self.assertEqual(self.strategy.strategy_type, StrategyType.BEAR_PUT_SPREAD)
    
    def test_two_legs(self):
        """Test strategy has two legs."""
        self.assertEqual(len(self.strategy.legs), 2)


class TestLongStraddle(unittest.TestCase):
    """Test cases for long straddle strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = create_long_straddle(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
    
    def test_strategy_type(self):
        """Test strategy type is correct."""
        self.assertEqual(self.strategy.strategy_type, StrategyType.LONG_STRADDLE)
    
    def test_two_legs(self):
        """Test strategy has two legs (call and put)."""
        self.assertEqual(len(self.strategy.legs), 2)
    
    def test_both_legs_long(self):
        """Test both legs are long."""
        self.assertTrue(all(leg.is_long for leg in self.strategy.legs))
    
    def test_two_breakevens(self):
        """Test straddle has two breakeven points."""
        breakevens = self.strategy.breakeven_points()
        
        self.assertEqual(len(breakevens), 2)
    
    def test_breakevens_straddle_strike(self):
        """Test breakevens are on either side of strike."""
        breakevens = sorted(self.strategy.breakeven_points())
        
        self.assertLess(breakevens[0], 100)
        self.assertGreater(breakevens[1], 100)


class TestIronCondor(unittest.TestCase):
    """Test cases for iron condor strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = create_iron_condor(
            underlying_price=100,
            put_lower_strike=85,
            put_upper_strike=95,
            call_lower_strike=105,
            call_upper_strike=115,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
    
    def test_strategy_type(self):
        """Test strategy type is correct."""
        self.assertEqual(self.strategy.strategy_type, StrategyType.IRON_CONDOR)
    
    def test_four_legs(self):
        """Test strategy has four legs."""
        self.assertEqual(len(self.strategy.legs), 4)
    
    def test_net_credit(self):
        """Test iron condor generates a credit."""
        # Iron condor should be a credit (negative cost)
        cost = self.strategy.total_cost()
        self.assertLess(cost, 0)
    
    def test_max_profit_equals_credit(self):
        """Test max profit equals net credit received."""
        max_profit = self.strategy.max_profit()
        credit = -self.strategy.total_cost()
        
        self.assertAlmostEqual(max_profit, credit, places=2)


class TestPortfolioGreeks(unittest.TestCase):
    """Test cases for portfolio Greeks calculation."""
    
    def test_single_leg_greeks(self):
        """Test Greeks for single leg strategy."""
        strategy = create_long_call(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
        
        greeks = strategy.portfolio_greeks()
        
        # Long call should have positive delta
        self.assertGreater(greeks.delta, 0)
        # Should have positive gamma
        self.assertGreater(greeks.gamma, 0)
        # Should have negative theta
        self.assertLess(greeks.theta, 0)
        # Should have positive vega
        self.assertGreater(greeks.vega, 0)
    
    def test_spread_reduced_greeks(self):
        """Test that spread has reduced Greeks compared to single leg."""
        single = create_long_call(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
        
        spread = create_bull_call_spread(
            underlying_price=100,
            lower_strike=95,
            upper_strike=105,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.2
        )
        
        single_greeks = single.portfolio_greeks()
        spread_greeks = spread.portfolio_greeks()
        
        # Spread should have lower vega (more volatility neutral)
        self.assertLess(abs(spread_greeks.vega), abs(single_greeks.vega))


if __name__ == "__main__":
    unittest.main()
