"""
Unit tests for the Black-Scholes pricing model.
"""

import unittest
import math
from options_trading.models.option import Option, OptionType
from options_trading.models.black_scholes import BlackScholes


class TestBlackScholes(unittest.TestCase):
    """Test cases for Black-Scholes pricing model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Standard test option parameters
        self.call_option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.put_option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
    
    def test_call_price_positive(self):
        """Test that call option price is positive."""
        price = BlackScholes.price(self.call_option)
        self.assertGreater(price, 0)
    
    def test_put_price_positive(self):
        """Test that put option price is positive."""
        price = BlackScholes.price(self.put_option)
        self.assertGreater(price, 0)
    
    def test_put_call_parity(self):
        """Test put-call parity: C - P = S - K*e^(-rT)."""
        call_price = BlackScholes.price(self.call_option)
        put_price = BlackScholes.price(self.put_option)
        
        S = self.call_option.underlying_price
        K = self.call_option.strike_price
        r = self.call_option.risk_free_rate
        T = self.call_option.time_to_expiry
        
        # C - P should equal S - K*e^(-rT)
        left_side = call_price - put_price
        right_side = S - K * math.exp(-r * T)
        
        self.assertAlmostEqual(left_side, right_side, places=6)
    
    def test_itm_call_has_intrinsic_value(self):
        """Test that deep ITM call has at least intrinsic value."""
        itm_call = Option(
            underlying_price=120,
            strike_price=100,
            time_to_expiry=0.5,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        price = BlackScholes.price(itm_call)
        intrinsic = 120 - 100
        
        self.assertGreaterEqual(price, intrinsic)
    
    def test_itm_put_has_significant_value(self):
        """Test that deep ITM put has significant value.
        
        Note: European put prices can be below intrinsic value due to 
        discounting of the strike price in the Black-Scholes formula.
        """
        itm_put = Option(
            underlying_price=80,
            strike_price=100,
            time_to_expiry=0.5,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
        
        price = BlackScholes.price(itm_put)
        intrinsic = 100 - 80
        
        # European put can be below intrinsic due to interest rate effects
        # but should be close to intrinsic for deep ITM
        self.assertGreater(price, intrinsic * 0.85)
    
    def test_at_expiry_call(self):
        """Test call option value at expiration."""
        expired_itm = Option(
            underlying_price=110,
            strike_price=100,
            time_to_expiry=0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        expired_otm = Option(
            underlying_price=90,
            strike_price=100,
            time_to_expiry=0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertAlmostEqual(BlackScholes.price(expired_itm), 10, places=6)
        self.assertAlmostEqual(BlackScholes.price(expired_otm), 0, places=6)
    
    def test_at_expiry_put(self):
        """Test put option value at expiration."""
        expired_itm = Option(
            underlying_price=90,
            strike_price=100,
            time_to_expiry=0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
        
        expired_otm = Option(
            underlying_price=110,
            strike_price=100,
            time_to_expiry=0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
        
        self.assertAlmostEqual(BlackScholes.price(expired_itm), 10, places=6)
        self.assertAlmostEqual(BlackScholes.price(expired_otm), 0, places=6)
    
    def test_call_delta_range(self):
        """Test that call delta is between 0 and 1."""
        delta = BlackScholes.delta(self.call_option)
        self.assertGreaterEqual(delta, 0)
        self.assertLessEqual(delta, 1)
    
    def test_put_delta_range(self):
        """Test that put delta is between -1 and 0."""
        delta = BlackScholes.delta(self.put_option)
        self.assertGreaterEqual(delta, -1)
        self.assertLessEqual(delta, 0)
    
    def test_atm_call_delta_approximately_half(self):
        """Test that ATM call delta is approximately 0.5."""
        delta = BlackScholes.delta(self.call_option)
        self.assertAlmostEqual(delta, 0.5, delta=0.15)
    
    def test_gamma_positive(self):
        """Test that gamma is always positive."""
        call_gamma = BlackScholes.gamma(self.call_option)
        put_gamma = BlackScholes.gamma(self.put_option)
        
        self.assertGreater(call_gamma, 0)
        self.assertGreater(put_gamma, 0)
    
    def test_gamma_call_put_equal(self):
        """Test that gamma is the same for call and put at same strike."""
        call_gamma = BlackScholes.gamma(self.call_option)
        put_gamma = BlackScholes.gamma(self.put_option)
        
        self.assertAlmostEqual(call_gamma, put_gamma, places=8)
    
    def test_theta_typically_negative(self):
        """Test that theta is typically negative for long options."""
        call_theta = BlackScholes.theta(self.call_option)
        put_theta = BlackScholes.theta(self.put_option)
        
        # For standard options, theta should be negative
        self.assertLess(call_theta, 0)
        # Put theta can be positive for deep ITM, but ATM should be negative
        self.assertLess(put_theta, 0)
    
    def test_vega_positive(self):
        """Test that vega is positive."""
        call_vega = BlackScholes.vega(self.call_option)
        put_vega = BlackScholes.vega(self.put_option)
        
        self.assertGreater(call_vega, 0)
        self.assertGreater(put_vega, 0)
    
    def test_vega_call_put_equal(self):
        """Test that vega is the same for call and put at same strike."""
        call_vega = BlackScholes.vega(self.call_option)
        put_vega = BlackScholes.vega(self.put_option)
        
        self.assertAlmostEqual(call_vega, put_vega, places=8)
    
    def test_rho_call_positive(self):
        """Test that call rho is positive."""
        rho = BlackScholes.rho(self.call_option)
        self.assertGreater(rho, 0)
    
    def test_rho_put_negative(self):
        """Test that put rho is negative."""
        rho = BlackScholes.rho(self.put_option)
        self.assertLess(rho, 0)
    
    def test_implied_volatility(self):
        """Test implied volatility calculation."""
        # Calculate theoretical price
        known_vol = 0.25
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=0.5,
            risk_free_rate=0.05,
            volatility=known_vol,
            option_type=OptionType.CALL
        )
        
        market_price = BlackScholes.price(option)
        
        # Calculate implied vol from price
        test_option = option.copy_with(volatility=0.1)  # Different initial vol
        implied_vol = BlackScholes.implied_volatility(test_option, market_price)
        
        self.assertAlmostEqual(implied_vol, known_vol, places=4)
    
    def test_implied_volatility_invalid_price(self):
        """Test that implied volatility raises error for invalid prices."""
        with self.assertRaises(ValueError):
            BlackScholes.implied_volatility(self.call_option, -1)
    
    def test_higher_volatility_higher_price(self):
        """Test that higher volatility leads to higher option prices."""
        low_vol_option = self.call_option.copy_with(volatility=0.1)
        high_vol_option = self.call_option.copy_with(volatility=0.5)
        
        low_price = BlackScholes.price(low_vol_option)
        high_price = BlackScholes.price(high_vol_option)
        
        self.assertGreater(high_price, low_price)
    
    def test_longer_time_higher_price(self):
        """Test that longer time to expiry leads to higher option prices (generally)."""
        short_term = self.call_option.copy_with(time_to_expiry=0.25)
        long_term = self.call_option.copy_with(time_to_expiry=1.0)
        
        short_price = BlackScholes.price(short_term)
        long_price = BlackScholes.price(long_term)
        
        self.assertGreater(long_price, short_price)


class TestBlackScholesEdgeCases(unittest.TestCase):
    """Test edge cases for Black-Scholes model."""
    
    def test_zero_volatility(self):
        """Test pricing with zero volatility."""
        option = Option(
            underlying_price=110,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0,
            option_type=OptionType.CALL
        )
        
        price = BlackScholes.price(option)
        # Should be close to discounted intrinsic value
        self.assertGreater(price, 0)
    
    def test_very_high_volatility(self):
        """Test pricing with very high volatility."""
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=3.0,  # 300% volatility
            option_type=OptionType.CALL
        )
        
        price = BlackScholes.price(option)
        self.assertGreater(price, 0)
        # Price should be bounded by underlying price
        self.assertLessEqual(price, option.underlying_price)
    
    def test_deep_otm_option(self):
        """Test pricing for deep out of the money option."""
        deep_otm = Option(
            underlying_price=50,
            strike_price=200,
            time_to_expiry=0.1,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        price = BlackScholes.price(deep_otm)
        # Should be very small but non-negative
        self.assertGreaterEqual(price, 0)
        self.assertLess(price, 1)
    
    def test_deep_itm_option(self):
        """Test pricing for deep in the money option."""
        deep_itm = Option(
            underlying_price=200,
            strike_price=50,
            time_to_expiry=0.1,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        price = BlackScholes.price(deep_itm)
        intrinsic = 200 - 50
        
        # Should be close to intrinsic value
        self.assertGreaterEqual(price, intrinsic * 0.99)


if __name__ == "__main__":
    unittest.main()
