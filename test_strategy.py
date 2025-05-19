"""
Test cases for the Short Strangle strategy.
"""

import unittest
from unittest.mock import patch, MagicMock
import datetime
import json

from src.strategies.short_strangle import ShortStrangleStrategy
from src.models.order import Order, OrderType, OrderSide, OrderStatus, ProductType, OptionType
from src.models.position import Position
from src.models.option_chain import OptionChain, OptionContract
from tests.test_utils import MockMStockAPI


class TestShortStrangleStrategy(unittest.TestCase):
    """Test cases for the Short Strangle strategy."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_api = MockMStockAPI()
        self.strategy = ShortStrangleStrategy(self.mock_api)
        
        # Set up mock data
        self.mock_api.set_mock_positions([
            {
                "tradingsymbol": "NIFTY25MAY18000CE",
                "exchange": "NFO",
                "instrument_token": "12345",
                "product": "NRML",
                "quantity": -75,
                "average_price": 150.25,
                "last_price": 155.50,
                "pnl": -393.75
            },
            {
                "tradingsymbol": "NIFTY25MAY17000PE",
                "exchange": "NFO",
                "instrument_token": "12346",
                "product": "NRML",
                "quantity": -75,
                "average_price": 145.75,
                "last_price": 140.25,
                "pnl": 412.50
            }
        ])
        
        self.mock_api.set_mock_option_chain_master({
            "dctExp": {
                "1": 1795876200,
                "2": 1716470400,
                "3": 1717075200,
                "4": 1717680000
            },
            "OPTIDX": [
                "NIFTY,26000,2,3,4"
            ]
        })
        
        self.mock_api.set_mock_option_chain({
            "contractModel": {
                "sym": "NIFTY",
                "spotPrice": 18500.25,
                "ce": [
                    {
                        "sym": "NIFTY25MAY18000CE",
                        "strikePrice": 18000,
                        "token": "12345",
                        "lastPrice": 155.50
                    },
                    {
                        "sym": "NIFTY25MAY19500CE",
                        "strikePrice": 19500,
                        "token": "12351",
                        "lastPrice": 30.50
                    }
                ],
                "pe": [
                    {
                        "sym": "NIFTY25MAY17000PE",
                        "strikePrice": 17000,
                        "token": "12346",
                        "lastPrice": 140.25
                    },
                    {
                        "sym": "NIFTY25MAY16500PE",
                        "strikePrice": 16500,
                        "token": "12352",
                        "lastPrice": 15.25
                    }
                ]
            }
        })
        
        self.mock_api.set_mock_fund_summary({
            "invested_amount": 150000,
            "available_funds": 50000
        })
    
    def test_initialize(self):
        """Test strategy initialization."""
        result = self.strategy.initialize()
        
        self.assertTrue(result)
        self.assertEqual(len(self.strategy.active_positions), 2)
        self.assertIn("NIFTY25MAY18000CE", self.strategy.active_positions)
        self.assertIn("NIFTY25MAY17000PE", self.strategy.active_positions)
    
    def test_calculate_investment_amount(self):
        """Test investment amount calculation."""
        investment = self.strategy.calculate_investment_amount()
        
        self.assertEqual(investment, 200000)  # 150000 invested + 50000 available
    
    @patch('src.strategies.short_strangle.get_expiry_date_n_weeks_ahead')
    def test_place_short_strangle(self, mock_get_expiry):
        """Test placing short strangle position."""
        # Mock expiry dates
        sell_expiry = datetime.date(2025, 6, 15)
        hedge_expiry = datetime.date(2025, 5, 25)
        mock_get_expiry.side_effect = lambda weeks, from_date=None: sell_expiry if weeks == 4 else hedge_expiry
        
        # Initialize strategy
        self.strategy.initialize()
        
        # Test placing short strangle
        result = self.strategy.place_short_strangle(200000)
        
        self.assertTrue(result)
        # Check that orders were placed
        self.assertEqual(len(self.strategy.placed_orders_cache), 4)  # 2 sell orders + 2 hedge orders
    
    def test_handle_stop_loss(self):
        """Test handling stop loss."""
        # Initialize strategy
        self.strategy.initialize()
        
        # Create a position with price drop > 25%
        position = Position(
            symbol="NIFTY25MAY18000CE",
            exchange="NFO",
            instrument_token="12345",
            quantity=-75,
            average_price=200.0,  # Original price
            last_price=140.0,  # 30% drop
            pnl=-4500.0,
            product="NRML",
            option_type=OptionType.CE
        )
        
        # Test handling stop loss
        result = self.strategy.handle_stop_loss(position)
        
        self.assertTrue(result)
        # Check that stop loss order was placed
        self.assertGreaterEqual(len(self.strategy.active_orders), 1)
    
    def test_handle_martingale(self):
        """Test handling martingale strategy."""
        # Initialize strategy
        self.strategy.initialize()
        
        # Create a position with price doubled
        position = Position(
            symbol="NIFTY25MAY18000CE",
            exchange="NFO",
            instrument_token="12345",
            quantity=-75,
            average_price=150.0,  # Original price
            last_price=310.0,  # More than doubled
            pnl=-12000.0,
            product="NRML",
            option_type=OptionType.CE,
            expiry_date=datetime.datetime(2025, 5, 25, 15, 30)
        )
        
        # Test handling martingale
        result = self.strategy.handle_martingale(position)
        
        self.assertTrue(result)
        # Check that martingale orders were placed
        self.assertGreaterEqual(len(self.strategy.active_orders), 1)
    
    @patch('src.strategies.short_strangle.get_expiry_date_n_weeks_ahead')
    @patch('src.strategies.short_strangle.datetime')
    def test_rollover_hedge(self, mock_datetime, mock_get_expiry):
        """Test rolling over hedge positions."""
        # Mock today as expiry day
        today = datetime.date(2025, 5, 25)
        mock_datetime.date.today.return_value = today
        
        # Mock expiry dates
        this_week_expiry = today
        next_week_expiry = datetime.date(2025, 6, 1)
        mock_get_expiry.side_effect = lambda weeks, from_date=None: this_week_expiry if weeks == 1 else next_week_expiry
        
        # Add hedge positions to mock API
        self.mock_api.set_mock_positions([
            {
                "tradingsymbol": "NIFTY25MAY18500CE",
                "exchange": "NFO",
                "instrument_token": "12347",
                "product": "NRML",
                "quantity": 75,
                "average_price": 95.25,
                "last_price": 98.50,
                "pnl": 243.75,
                "is_hedge": True,
                "expiry_date": datetime.datetime(2025, 5, 25, 15, 30)
            },
            {
                "tradingsymbol": "NIFTY25MAY17500PE",
                "exchange": "NFO",
                "instrument_token": "12348",
                "product": "NRML",
                "quantity": 75,
                "average_price": 45.50,
                "last_price": 42.75,
                "pnl": -206.25,
                "is_hedge": True,
                "expiry_date": datetime.datetime(2025, 5, 25, 15, 30)
            }
        ])
        
        # Initialize strategy
        self.strategy.initialize()
        
        # Test rolling over hedge positions
        result = self.strategy.rollover_hedge()
        
        self.assertTrue(result)
        # Check that rollover orders were placed
        self.assertGreaterEqual(len(self.strategy.active_orders), 2)
    
    def test_negative_api_failure(self):
        """Test handling API failures."""
        # Set up API to return None for positions
        self.mock_api.set_mock_positions(None)
        
        # Initialize strategy should fail
        result = self.strategy.initialize()
        
        self.assertFalse(result)
    
    def test_negative_empty_option_chain(self):
        """Test handling empty option chain."""
        # Set up API to return empty option chain
        self.mock_api.set_mock_option_chain({
            "contractModel": {
                "sym": "NIFTY",
                "spotPrice": 18500.25,
                "ce": [],
                "pe": []
            }
        })
        
        # Initialize strategy
        self.strategy.initialize()
        
        # Test placing short strangle should fail
        with patch('src.strategies.short_strangle.get_expiry_date_n_weeks_ahead') as mock_get_expiry:
            # Mock expiry dates
            sell_expiry = datetime.date(2025, 6, 15)
            hedge_expiry = datetime.date(2025, 5, 25)
            mock_get_expiry.side_effect = lambda weeks, from_date=None: sell_expiry if weeks == 4 else hedge_expiry
            
            result = self.strategy.place_short_strangle(200000)
            
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
