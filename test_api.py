"""
Test cases for the MStockAPI client.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import datetime

from src.api.mstock_api import MStockAPI
from tests.test_utils import mock_api_response, mock_api_error_response, MockResponse


class TestMStockAPI(unittest.TestCase):
    """Test cases for the MStockAPI client."""
    
    def setUp(self):
        """Set up test environment."""
        self.api = MStockAPI("test_api_key", "test_username", "test_password")
    
    @patch('requests.post')
    def test_login_success(self, mock_post):
        """Test successful login."""
        # Mock the login response
        mock_post.side_effect = lambda url, headers, data: mock_api_response(url, headers, data)
        
        # Mock input function to return OTP
        with patch('builtins.input', return_value="123456"):
            result = self.api.login()
        
        self.assertTrue(result)
        self.assertEqual(self.api.access_token, "test_access_token")
        self.assertIn("Authorization", self.api.headers)
        self.assertEqual(self.api.headers["Authorization"], "token test_api_key:test_access_token")
    
    @patch('requests.post')
    def test_login_failure(self, mock_post):
        """Test login failure."""
        # Mock the login error response
        mock_post.side_effect = lambda url, headers, data: mock_api_error_response(url, headers, data)
        
        result = self.api.login()
        
        self.assertFalse(result)
        self.assertIsNone(self.api.access_token)
    
    @patch('requests.get')
    def test_get_positions_success(self, mock_get):
        """Test successful get positions."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the positions response
        mock_get.side_effect = lambda url, headers: mock_api_response(url, headers)
        
        positions = self.api.get_positions()
        
        self.assertIsNotNone(positions)
        self.assertEqual(len(positions), 2)
        self.assertEqual(positions[0]["tradingsymbol"], "NIFTY25MAY18000CE")
        self.assertEqual(positions[1]["tradingsymbol"], "NIFTY25MAY17000PE")
    
    @patch('requests.get')
    def test_get_positions_failure(self, mock_get):
        """Test get positions failure."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the positions error response
        mock_get.side_effect = lambda url, headers: mock_api_error_response(url, headers)
        
        positions = self.api.get_positions()
        
        self.assertIsNone(positions)
    
    @patch('requests.get')
    def test_get_option_chain_master_success(self, mock_get):
        """Test successful get option chain master."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the option chain master response
        mock_get.side_effect = lambda url, headers: mock_api_response(url, headers)
        
        option_chain_master = self.api.get_option_chain_master()
        
        self.assertIsNotNone(option_chain_master)
        self.assertIn("dctExp", option_chain_master)
        self.assertIn("OPTIDX", option_chain_master)
        self.assertEqual(option_chain_master["OPTIDX"][0], "NIFTY,26000,2,3,4")
    
    @patch('requests.get')
    def test_get_option_chain_success(self, mock_get):
        """Test successful get option chain."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the option chain response
        mock_get.side_effect = lambda url, headers: mock_api_response(url, headers)
        
        option_chain = self.api.get_option_chain("1716470400", "26000")
        
        self.assertIsNotNone(option_chain)
        self.assertIn("contractModel", option_chain)
        self.assertEqual(option_chain["contractModel"]["sym"], "NIFTY")
        self.assertEqual(len(option_chain["contractModel"]["ce"]), 4)
        self.assertEqual(len(option_chain["contractModel"]["pe"]), 4)
    
    @patch('requests.post')
    def test_place_order_success(self, mock_post):
        """Test successful place order."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the place order response
        mock_post.side_effect = lambda url, headers, data: mock_api_response(url, headers, data)
        
        order_params = {
            "tradingsymbol": "NIFTY25MAY18000CE",
            "exchange": "NFO",
            "transaction_type": "SELL",
            "order_type": "MARKET",
            "quantity": "75",
            "product": "NRML",
            "validity": "DAY"
        }
        
        response = self.api.place_order(order_params)
        
        self.assertIsNotNone(response)
        self.assertEqual(response["order_id"], "test_order_123")
        self.assertEqual(response["status"], "OPEN")
    
    @patch('requests.post')
    def test_place_order_failure(self, mock_post):
        """Test place order failure."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the place order error response
        mock_post.side_effect = lambda url, headers, data: mock_api_error_response(url, headers, data)
        
        order_params = {
            "tradingsymbol": "NIFTY25MAY18000CE",
            "exchange": "NFO",
            "transaction_type": "SELL",
            "order_type": "MARKET",
            "quantity": "75",
            "product": "NRML",
            "validity": "DAY"
        }
        
        response = self.api.place_order(order_params)
        
        self.assertIsNone(response)
    
    @patch('requests.get')
    def test_get_fund_summary_success(self, mock_get):
        """Test successful get fund summary."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the fund summary response
        mock_get.side_effect = lambda url, headers: mock_api_response(url, headers)
        
        fund_summary = self.api.get_fund_summary()
        
        self.assertIsNotNone(fund_summary)
        self.assertEqual(fund_summary["invested_amount"], 150000)
        self.assertEqual(fund_summary["available_funds"], 50000)
    
    @patch('requests.post')
    def test_cancel_order_success(self, mock_post):
        """Test successful cancel order."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the cancel order response
        mock_post.side_effect = lambda url, headers, data: mock_api_response(url, headers, data)
        
        result = self.api.cancel_order("test_order_123")
        
        self.assertTrue(result)
    
    @patch('requests.post')
    def test_cancel_order_failure(self, mock_post):
        """Test cancel order failure."""
        # Set up API with access token
        self.api.access_token = "test_access_token"
        self.api.headers["Authorization"] = f"token {self.api.api_key}:{self.api.access_token}"
        
        # Mock the cancel order error response
        mock_post.side_effect = lambda url, headers, data: mock_api_error_response(url, headers, data)
        
        result = self.api.cancel_order("test_order_123")
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
