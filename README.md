# Options Trading System

A comprehensive Python-based options trading system with pricing models, Greeks calculations, trading strategies, and portfolio management.

## Features

- **Black-Scholes Pricing Model**: Analytical pricing for European call and put options
- **Greeks Calculations**: Delta, Gamma, Theta, Vega, and Rho
- **Implied Volatility**: Newton-Raphson and bisection methods for IV calculation
- **Trading Strategies**: 
  - Single leg: Long/Short Call, Long/Short Put
  - Spreads: Bull Call, Bear Put, Bull Put, Bear Call
  - Volatility: Long/Short Straddle, Long/Short Strangle
  - Income: Iron Condor, Iron Butterfly
- **Portfolio Management**: Position tracking, P&L calculation, risk metrics

## Installation

```bash
# Clone the repository
git clone https://github.com/acraajkumar/Data.git
cd Data

# Install the package
pip install -e .
```

## Quick Start

### Basic Option Pricing

```python
from options_trading import Option, OptionType, BlackScholes

# Create a call option
call = Option(
    underlying_price=100,      # Current stock price
    strike_price=100,          # Strike price
    time_to_expiry=0.25,       # 3 months (in years)
    risk_free_rate=0.05,       # 5% annual rate
    volatility=0.20,           # 20% annual volatility
    option_type=OptionType.CALL
)

# Calculate the theoretical price
price = BlackScholes.price(call)
print(f"Call Option Price: ${price:.2f}")
```

### Calculate Greeks

```python
from options_trading import Greeks

# Calculate all Greeks at once
greeks = Greeks.calculate(call)
print(greeks)

# Or calculate individually
delta = BlackScholes.delta(call)
gamma = BlackScholes.gamma(call)
theta = BlackScholes.theta(call)
vega = BlackScholes.vega(call)
rho = BlackScholes.rho(call)

print(f"Delta: {delta:.4f}")
print(f"Gamma: {gamma:.6f}")
print(f"Theta: {theta:.4f} per year")
print(f"Vega: {vega:.4f} per 1%")
print(f"Rho: {rho:.4f} per 1%")
```

### Implied Volatility

```python
# Calculate implied volatility from market price
market_price = 5.50
implied_vol = BlackScholes.implied_volatility(call, market_price)
print(f"Implied Volatility: {implied_vol:.2%}")
```

### Trading Strategies

```python
from options_trading.strategies import (
    create_long_call,
    create_bull_call_spread,
    create_iron_condor
)

# Create a bull call spread
spread = create_bull_call_spread(
    underlying_price=100,
    lower_strike=95,
    upper_strike=105,
    time_to_expiry=0.25,
    risk_free_rate=0.05,
    volatility=0.20
)

print(f"Net Cost: ${spread.total_cost():.2f}")
print(f"Max Profit: ${spread.max_profit():.2f}")
print(f"Max Loss: ${spread.max_loss():.2f}")
print(f"Breakeven Points: {spread.breakeven_points()}")

# Create an iron condor
condor = create_iron_condor(
    underlying_price=100,
    put_lower_strike=85,
    put_upper_strike=95,
    call_lower_strike=105,
    call_upper_strike=115,
    time_to_expiry=0.25,
    risk_free_rate=0.05,
    volatility=0.20
)

print(condor)
```

### Portfolio Management

```python
from options_trading import Portfolio, Option, OptionType
from options_trading.portfolio import PositionSide

# Create a portfolio
portfolio = Portfolio(name="My Options Portfolio", cash_balance=100000)

# Add positions
call_option = Option(
    underlying_price=100,
    strike_price=105,
    time_to_expiry=0.5,
    risk_free_rate=0.05,
    volatility=0.25,
    option_type=OptionType.CALL
)

position = portfolio.add_position(
    option=call_option,
    quantity=10,
    side=PositionSide.LONG,
    entry_price=3.50
)

# View portfolio summary
print(portfolio)

# Get risk summary
risk = portfolio.risk_summary()
print(f"Net Liquidation Value: ${risk['net_liquidation_value']:,.2f}")
print(f"Delta Exposure: {risk['delta_exposure']:.2f}")
print(f"Daily Theta Decay: ${risk['theta_daily']:.2f}")
```

## Module Structure

```
options_trading/
├── __init__.py              # Package initialization
├── portfolio.py             # Portfolio management
├── models/
│   ├── __init__.py
│   ├── option.py            # Option class and enums
│   ├── black_scholes.py     # Black-Scholes pricing model
│   └── greeks.py            # Greeks calculations
├── strategies/
│   ├── __init__.py
│   └── strategy.py          # Trading strategies
├── utils/
│   ├── __init__.py
│   └── validators.py        # Input validation utilities
└── tests/
    ├── __init__.py
    ├── test_black_scholes.py
    ├── test_option.py
    ├── test_strategy.py
    └── test_portfolio.py
```

## Running Tests

```bash
# Run all tests
python -m pytest options_trading/tests/ -v

# Run specific test file
python -m pytest options_trading/tests/test_black_scholes.py -v

# Run with coverage
python -m pytest options_trading/tests/ --cov=options_trading
```

## Mathematical Background

### Black-Scholes Formula

For a European call option:
```
C = S₀ × N(d₁) - K × e^(-rT) × N(d₂)
```

For a European put option:
```
P = K × e^(-rT) × N(-d₂) - S₀ × N(-d₁)
```

Where:
- `d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)`
- `d₂ = d₁ - σ√T`
- `S₀` = Current stock price
- `K` = Strike price
- `T` = Time to expiration (in years)
- `r` = Risk-free interest rate
- `σ` = Volatility
- `N(x)` = Standard normal cumulative distribution function

### Greeks Definitions

| Greek | Definition | Interpretation |
|-------|------------|----------------|
| Delta (Δ) | ∂V/∂S | Change in option price per $1 change in underlying |
| Gamma (Γ) | ∂²V/∂S² | Change in delta per $1 change in underlying |
| Theta (Θ) | ∂V/∂t | Change in option price per day (time decay) |
| Vega (ν) | ∂V/∂σ | Change in option price per 1% change in volatility |
| Rho (ρ) | ∂V/∂r | Change in option price per 1% change in interest rate |

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This software is for educational purposes only. Options trading involves significant risk of loss. Always consult with a qualified financial advisor before making investment decisions.
