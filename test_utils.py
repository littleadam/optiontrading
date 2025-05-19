"""
Test utilities for mocking API responses and testing the trading application.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional, Callable

from src.api.mstock_api import MStockAPI


class MockResponse:
    """Mock response object for API calls."""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int):
        """
        Initialize the mock response.
        
        Args:
            json_data: JSON data to return
            status_code: HTTP status code
        """
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
    
    def json(self) -> Dict[str, Any]:
        """
        Get JSON data.
        
        Returns:
            JSON data
        """
        return self.json_data


def mock_api_response(url: str, headers: Dict[str, str] = None, data: Dict[str, Any] = None) -> MockResponse:
    """
    Mock API response based on URL and data.
    
    Args:
        url: API URL
        headers: Request headers
        data: Request data
        
    Returns:
        MockResponse object
    """
    # Default success response
    response = {
        "status": "success",
        "data": {}
    }
    
    # Mock different API endpoints
    if "login" in url:
        response["data"] = {
            "ugid": "test-ugid",
            "is_kyc": "true",
            "is_activate": "true",
            "is_password_reset": "true",
            "is_error": "false",
            "cid": "TEST123",
            "nm": "Test User",
            "flag": 0
        }
    elif "session/token" in url:
        response["data"] = {
            "user_type": "individual",
            "email": "test@example.com",
            "user_name": "testuser",
            "user_shortname": "Test",
            "broker": "MIRAE",
            "exchanges": ["NSE", "NFO", "CDS"],
            "products": ["CNC", "NRML", "MIS"],
            "order_types": ["MARKET", "LIMIT"],
            "avatar_url": "",
            "user_id": "123",
            "api_key": "test_api_key",
            "access_token": "test_access_token",
            "public_token": "test_public_token",
            "enctoken": "test_enctoken",
            "refresh_token": "test_refresh_token",
            "silo": "",
            "login_time": "2025-05-18 02:28:00"
        }
    elif "positions" in url:
        response["data"] = {
            "net": [
                {
                    "tradingsymbol": "NIFTY25MAY18000CE",
                    "exchange": "NFO",
                    "instrument_token": "12345",
                    "product": "NRML",
                    "quantity": -75,
                    "overnight_quantity": 0,
                    "multiplier": 1,
                    "average_price": 150.25,
                    "close_price": 155.50,
                    "last_price": 155.50,
                    "value": -11268.75,
                    "pnl": -393.75,
                    "m2m": -393.75,
                    "unrealised": -393.75,
                    "realised": 0,
                    "buy_quantity": 0,
                    "buy_price": 0,
                    "buy_value": 0,
                    "buy_m2m": 0,
                    "sell_quantity": 75,
                    "sell_price": 150.25,
                    "sell_value": 11268.75,
                    "sell_m2m": 0,
                    "day_buy_quantity": 0,
                    "day_buy_price": 0,
                    "day_buy_value": 0,
                    "day_sell_quantity": 75,
                    "day_sell_price": 150.25,
                    "day_sell_value": 11268.75
                },
                {
                    "tradingsymbol": "NIFTY25MAY17000PE",
                    "exchange": "NFO",
                    "instrument_token": "12346",
                    "product": "NRML",
                    "quantity": -75,
                    "overnight_quantity": 0,
                    "multiplier": 1,
                    "average_price": 145.75,
                    "close_price": 140.25,
                    "last_price": 140.25,
                    "value": -10931.25,
                    "pnl": 412.50,
                    "m2m": 412.50,
                    "unrealised": 412.50,
                    "realised": 0,
                    "buy_quantity": 0,
                    "buy_price": 0,
                    "buy_value": 0,
                    "buy_m2m": 0,
                    "sell_quantity": 75,
                    "sell_price": 145.75,
                    "sell_value": 10931.25,
                    "sell_m2m": 0,
                    "day_buy_quantity": 0,
                    "day_buy_price": 0,
                    "day_buy_value": 0,
                    "day_sell_quantity": 75,
                    "day_sell_price": 145.75,
                    "day_sell_value": 10931.25
                }
            ],
            "day": None
        }
    elif "getoptionchainmaster" in url:
        response["data"] = {
            "dctExp": {
                "1": 1795876200,  # Example timestamps for different expiry dates
                "2": 1716470400,
                "3": 1717075200,
                "4": 1717680000
            },
            "OPTIDX": [
                "NIFTY,26000,2,3,4"
            ]
        }
    elif "GetOptionChain" in url:
        response["data"] = {
            "contractModel": {
                "sym": "NIFTY",
                "spotPrice": 18500.25,
                "ce": [
                    {
                        "sym": "NIFTY25MAY18000CE",
                        "strikePrice": 18000,
                        "token": "12345",
                        "lastPrice": 155.50,
                        "change": 3.5,
                        "openInterest": 12500,
                        "volume": 8750,
                        "bidPrice": 154.75,
                        "bidQty": 150,
                        "askPrice": 156.25,
                        "askQty": 225
                    },
                    {
                        "sym": "NIFTY25MAY18500CE",
                        "strikePrice": 18500,
                        "token": "12347",
                        "lastPrice": 95.25,
                        "change": 2.75,
                        "openInterest": 15000,
                        "volume": 10500,
                        "bidPrice": 94.50,
                        "bidQty": 175,
                        "askPrice": 96.00,
                        "askQty": 250
                    },
                    {
                        "sym": "NIFTY25MAY19000CE",
                        "strikePrice": 19000,
                        "token": "12349",
                        "lastPrice": 55.75,
                        "change": 1.25,
                        "openInterest": 18000,
                        "volume": 12000,
                        "bidPrice": 55.25,
                        "bidQty": 200,
                        "askPrice": 56.25,
                        "askQty": 300
                    },
                    {
                        "sym": "NIFTY25MAY19500CE",
                        "strikePrice": 19500,
                        "token": "12351",
                        "lastPrice": 30.50,
                        "change": 0.75,
                        "openInterest": 20000,
                        "volume": 13500,
                        "bidPrice": 30.25,
                        "bidQty": 225,
                        "askPrice": 30.75,
                        "askQty": 325
                    }
                ],
                "pe": [
                    {
                        "sym": "NIFTY25MAY18000PE",
                        "strikePrice": 18000,
                        "token": "12346",
                        "lastPrice": 75.25,
                        "change": -2.5,
                        "openInterest": 13500,
                        "volume": 9250,
                        "bidPrice": 74.75,
                        "bidQty": 175,
                        "askPrice": 75.75,
                        "askQty": 250
                    },
                    {
                        "sym": "NIFTY25MAY17500PE",
                        "strikePrice": 17500,
                        "token": "12348",
                        "lastPrice": 45.50,
                        "change": -1.75,
                        "openInterest": 16000,
                        "volume": 11000,
                        "bidPrice": 45.00,
                        "bidQty": 200,
                        "askPrice": 46.00,
                        "askQty": 275
                    },
                    {
                        "sym": "NIFTY25MAY17000PE",
                        "strikePrice": 17000,
                        "token": "12350",
                        "lastPrice": 25.75,
                        "change": -1.00,
                        "openInterest": 19000,
                        "volume": 12500,
                        "bidPrice": 25.50,
                        "bidQty": 225,
                        "askPrice": 26.00,
                        "askQty": 300
                    },
                    {
                        "sym": "NIFTY25MAY16500PE",
                        "strikePrice": 16500,
                        "token": "12352",
                        "lastPrice": 15.25,
                        "change": -0.50,
                        "openInterest": 21000,
                        "volume": 14000,
                        "bidPrice": 15.00,
                        "bidQty": 250,
                        "askPrice": 15.50,
                        "askQty": 350
                    }
                ]
            }
        }
    elif "order/place" in url:
        response["data"] = {
            "order_id": "test_order_123",
            "status": "OPEN"
        }
    elif "order/modify" in url:
        response["data"] = {
            "order_id": "test_order_123",
            "status": "MODIFIED"
        }
    elif "order/cancel" in url:
        response["data"] = {
            "order_id": "test_order_123",
            "status": "CANCELLED"
        }
    elif "order/history" in url:
        response["data"] = [
            {
                "order_id": "test_order_123",
                "status": "COMPLETE",
                "tradingsymbol": "NIFTY25MAY18000CE",
                "exchange": "NFO",
                "transaction_type": "SELL",
                "order_type": "MARKET",
                "quantity": 75,
                "product": "NRML",
                "price": 0,
                "average_price": 150.25,
                "filled_quantity": 75,
                "pending_quantity": 0,
                "order_timestamp": "2025-05-18T02:28:00+05:30",
                "exchange_timestamp": "2025-05-18T02:28:05+05:30"
            }
        ]
    elif "fund/summary" in url:
        response["data"] = {
            "invested_amount": 150000,
            "available_funds": 50000,
            "total_margin_used": 25000,
            "margin_available": 175000
        }
    
    return MockResponse(response, 200)


def mock_api_error_response(url: str, headers: Dict[str, str] = None, data: Dict[str, Any] = None) -> MockResponse:
    """
    Mock API error response.
    
    Args:
        url: API URL
        headers: Request headers
        data: Request data
        
    Returns:
        MockResponse object with error
    """
    response = {
        "status": "error",
        "message": "API error for testing",
        "error_type": "TestException",
        "data": None
    }
    
    return MockResponse(response, 400)


class MockMStockAPI(MStockAPI):
    """Mock MStockAPI for testing."""
    
    def __init__(self):
        """Initialize the mock API."""
        # Don't call super().__init__() to avoid actual API calls
        self.api_key = "test_api_key"
        self.username = "test_username"
        self.password = "test_password"
        self.access_token = "test_access_token"
        self.headers = {
            "X-Mirae-Version": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "token test_api_key:test_access_token"
        }
        self.base_url = "https://api.mstock.trade"
        self.ws_url = "https://ws.mstock.trade"
        
        # Mock responses
        self.mock_positions = []
        self.mock_option_chain_master = {}
        self.mock_option_chain = {}
        self.mock_fund_summary = {}
        self.mock_order_history = []
        
    def login(self) -> bool:
        """Mock login."""
        return True
    
    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """Mock get positions."""
        return self.mock_positions
    
    def get_option_chain_master(self) -> Optional[Dict[str, Any]]:
        """Mock get option chain master."""
        return self.mock_option_chain_master
    
    def get_option_chain(self, expiry_timestamp: str, token: str) -> Optional[Dict[str, Any]]:
        """Mock get option chain."""
        return self.mock_option_chain
    
    def place_order(self, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock place order."""
        return {"order_id": "test_order_123", "status": "OPEN"}
    
    def modify_order(self, order_id: str, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock modify order."""
        return {"order_id": order_id, "status": "MODIFIED"}
    
    def cancel_order(self, order_id: str) -> bool:
        """Mock cancel order."""
        return True
    
    def get_order_history(self) -> Optional[List[Dict[str, Any]]]:
        """Mock get order history."""
        return self.mock_order_history
    
    def get_fund_summary(self) -> Optional[Dict[str, Any]]:
        """Mock get fund summary."""
        return self.mock_fund_summary
    
    def set_mock_positions(self, positions: List[Dict[str, Any]]) -> None:
        """Set mock positions."""
        self.mock_positions = positions
    
    def set_mock_option_chain_master(self, option_chain_master: Dict[str, Any]) -> None:
        """Set mock option chain master."""
        self.mock_option_chain_master = option_chain_master
    
    def set_mock_option_chain(self, option_chain: Dict[str, Any]) -> None:
        """Set mock option chain."""
        self.mock_option_chain = option_chain
    
    def set_mock_fund_summary(self, fund_summary: Dict[str, Any]) -> None:
        """Set mock fund summary."""
        self.mock_fund_summary = fund_summary
    
    def set_mock_order_history(self, order_history: List[Dict[str, Any]]) -> None:
        """Set mock order history."""
        self.mock_order_history = order_history
