"""
Unit tests for the Option class.
"""

import unittest
from options_trading.models.option import Option, OptionType


class TestOption(unittest.TestCase):
    """Test cases for the Option class."""
    
    def test_create_call_option(self):
        """Test creating a call option."""
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertEqual(option.underlying_price, 100)
        self.assertEqual(option.strike_price, 100)
        self.assertEqual(option.option_type, OptionType.CALL)
        self.assertTrue(option.is_call)
        self.assertFalse(option.is_put)
    
    def test_create_put_option(self):
        """Test creating a put option."""
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
        
        self.assertTrue(option.is_put)
        self.assertFalse(option.is_call)
    
    def test_invalid_underlying_price(self):
        """Test that negative underlying price raises error."""
        with self.assertRaises(ValueError):
            Option(
                underlying_price=-100,
                strike_price=100,
                time_to_expiry=1.0,
                risk_free_rate=0.05,
                volatility=0.2,
                option_type=OptionType.CALL
            )
    
    def test_invalid_strike_price(self):
        """Test that negative strike price raises error."""
        with self.assertRaises(ValueError):
            Option(
                underlying_price=100,
                strike_price=0,
                time_to_expiry=1.0,
                risk_free_rate=0.05,
                volatility=0.2,
                option_type=OptionType.CALL
            )
    
    def test_invalid_time_to_expiry(self):
        """Test that negative time to expiry raises error."""
        with self.assertRaises(ValueError):
            Option(
                underlying_price=100,
                strike_price=100,
                time_to_expiry=-0.5,
                risk_free_rate=0.05,
                volatility=0.2,
                option_type=OptionType.CALL
            )
    
    def test_invalid_volatility(self):
        """Test that negative volatility raises error."""
        with self.assertRaises(ValueError):
            Option(
                underlying_price=100,
                strike_price=100,
                time_to_expiry=1.0,
                risk_free_rate=0.05,
                volatility=-0.2,
                option_type=OptionType.CALL
            )
    
    def test_moneyness_atm(self):
        """Test moneyness calculation for ATM option."""
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertEqual(option.moneyness, 1.0)
    
    def test_moneyness_itm_call(self):
        """Test moneyness for ITM call."""
        option = Option(
            underlying_price=110,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertEqual(option.moneyness, 1.1)
        self.assertTrue(option.is_in_the_money())
    
    def test_moneyness_otm_call(self):
        """Test moneyness for OTM call."""
        option = Option(
            underlying_price=90,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertEqual(option.moneyness, 0.9)
        self.assertTrue(option.is_out_of_the_money())
    
    def test_intrinsic_value_itm_call(self):
        """Test intrinsic value for ITM call."""
        option = Option(
            underlying_price=120,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertEqual(option.intrinsic_value, 20)
    
    def test_intrinsic_value_otm_call(self):
        """Test intrinsic value for OTM call is zero."""
        option = Option(
            underlying_price=80,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertEqual(option.intrinsic_value, 0)
    
    def test_intrinsic_value_itm_put(self):
        """Test intrinsic value for ITM put."""
        option = Option(
            underlying_price=80,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
        
        self.assertEqual(option.intrinsic_value, 20)
    
    def test_intrinsic_value_otm_put(self):
        """Test intrinsic value for OTM put is zero."""
        option = Option(
            underlying_price=120,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.PUT
        )
        
        self.assertEqual(option.intrinsic_value, 0)
    
    def test_is_at_the_money(self):
        """Test ATM detection."""
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertTrue(option.is_at_the_money())
    
    def test_is_at_the_money_with_tolerance(self):
        """Test ATM detection with tolerance."""
        option = Option(
            underlying_price=100.5,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        self.assertTrue(option.is_at_the_money(tolerance=0.01))
        self.assertFalse(option.is_at_the_money(tolerance=0.001))
    
    def test_copy_with(self):
        """Test creating a copy with modified parameters."""
        original = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        modified = original.copy_with(underlying_price=110, volatility=0.3)
        
        # Check modified values
        self.assertEqual(modified.underlying_price, 110)
        self.assertEqual(modified.volatility, 0.3)
        
        # Check unchanged values
        self.assertEqual(modified.strike_price, 100)
        self.assertEqual(modified.time_to_expiry, 1.0)
        self.assertEqual(modified.risk_free_rate, 0.05)
        
        # Check original unchanged
        self.assertEqual(original.underlying_price, 100)
        self.assertEqual(original.volatility, 0.2)
    
    def test_string_representation(self):
        """Test string representation of option."""
        option = Option(
            underlying_price=100,
            strike_price=100,
            time_to_expiry=1.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type=OptionType.CALL
        )
        
        string_repr = str(option)
        self.assertIn("CALL", string_repr)
        self.assertIn("100.00", string_repr)


class TestOptionType(unittest.TestCase):
    """Test cases for OptionType enum."""
    
    def test_call_value(self):
        """Test call enum value."""
        self.assertEqual(OptionType.CALL.value, "call")
    
    def test_put_value(self):
        """Test put enum value."""
        self.assertEqual(OptionType.PUT.value, "put")


if __name__ == "__main__":
    unittest.main()
