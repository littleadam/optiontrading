"""
README for Nifty 50 Trading Application

This application implements a short strangle options trading strategy for Nifty 50 with specific rules for position management, stop loss, and martingale strategy.

## Features

- Short strangle strategy with legs at least 1000 points away from spot price
- 4-week expiry for sell orders and weekly expiry for hedge buy orders
- Weekly rollover of hedge positions
- 90% stop loss when a sell order drops by 25%
- Martingale strategy when a sell leg doubles in price
- Configurable parameters for all strategy components
- Comprehensive error handling and logging
- Extensive test coverage

## Project Structure

```
nifty_trading_app/
├── config/
│   └── config.py             # Configuration parameters
├── logs/                     # Log files directory (created at runtime)
├── src/
│   ├── api/
│   │   └── mstock_api.py     # mStock API client
│   ├── models/
│   │   ├── order.py          # Order model
│   │   ├── position.py       # Position model
│   │   └── option_chain.py   # Option chain model
│   ├── strategies/
│   │   └── short_strangle.py # Short strangle strategy implementation
│   └── utils/
│       ├── date_utils.py     # Date utility functions
│       ├── error_handler.py  # Error handling utilities
│       ├── logger.py         # Logging configuration
│       └── option_utils.py   # Option trading utilities
├── tests/
│   ├── test_api.py           # Tests for API client
│   ├── test_strategy.py      # Tests for strategy implementation
│   ├── test_strategies.py    # Test runner script
│   └── test_utils.py         # Test utilities
└── main.py                   # Main entry point
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install requests
   ```
3. Configure the application:
   - Edit `config/config.py` to set your API key and other parameters
   - Add holiday dates in the `HOLIDAYS` list

## Usage

### Running Tests

```
python tests/test_strategies.py
```

### Running the Application

```
python main.py --username YOUR_USERNAME --password YOUR_PASSWORD --api-key YOUR_API_KEY
```

Or set environment variables:
```
export MSTOCK_USERNAME=YOUR_USERNAME
export MSTOCK_PASSWORD=YOUR_PASSWORD
export MSTOCK_API_KEY=YOUR_API_KEY
python main.py
```

## Configuration

All strategy parameters are configurable in `config/config.py`:

- `API_CONFIG`: API connection settings
- `INVESTMENT_CONFIG`: Investment and lot size settings
- `STRATEGY_CONFIG`: Strategy parameters like target return, stop loss triggers, etc.
- `TRADING_HOURS`: Trading hours and check interval
- `HOLIDAYS`: List of market holidays
- `LOGGING_CONFIG`: Logging settings

## Strategy Logic

1. The application calculates the total investment amount (invested + available funds)
2. It places short strangle positions with legs at least 1000 points away from spot price
3. Each leg premium targets around 2% of the investment
4. Hedge buy orders are placed for the current week expiry
5. When a sell order drops by 25%, a 90% stop loss is placed and a new sell order is added
6. When a sell leg doubles in price (loss), a martingale strategy is implemented
7. Hedge positions are rolled over weekly on expiry day

## Error Handling

The application includes robust error handling with:
- Retry mechanisms for API failures
- Guards against empty instrument lists and bad LTP values
- Detailed logging with separate error logs
- Safe execution wrappers for critical functions

## Testing

The application includes comprehensive tests covering:
- API client functionality
- Strategy logic
- Error handling
- Edge cases and negative scenarios

Tests use mock API responses for offline testability.
"""
