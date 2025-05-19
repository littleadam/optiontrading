"""
mStock API client for interacting with the mStock Trading API.
Handles authentication, session management, and API requests.
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

from config.config import API_CONFIG

logger = logging.getLogger(__name__)

class MStockAPI:
    """
    Client for interacting with the mStock Trading API.
    Handles authentication, session management, and API requests.
    """
    
    def __init__(self, api_key: str, username: str, password: str):
        """
        Initialize the MStockAPI client.
        
        Args:
            api_key: API key for authentication
            username: mStock account username
            password: mStock account password
        """
        self.api_key = api_key
        self.username = username
        self.password = password
        self.access_token = None
        self.headers = {
            "X-Mirae-Version": API_CONFIG["version"],
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.base_url = API_CONFIG["api_url"]
        self.ws_url = API_CONFIG["ws_url"]
        
    def login(self) -> bool:
        """
        Login to mStock API and generate access token.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Step 1: Login with username and password to get OTP
            login_url = f"{self.base_url}/openapi/typea/connect/login"
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(login_url, headers=self.headers, data=login_data)
            if response.status_code != 200:
                logger.error(f"Login failed: {response.text}")
                return False
            
            login_response = response.json()
            if login_response["status"] != "success":
                logger.error(f"Login failed: {login_response['message']}")
                return False
            
            # Step 2: Get OTP from user (in production, this would be automated)
            otp = input("Enter the OTP sent to your registered mobile number: ")
            
            # Step 3: Generate session token
            session_url = f"{self.base_url}/openapi/typea/session/token"
            session_data = {
                "api_key": self.api_key,
                "request_token": otp,
                "checksum": "L"  # This might need to be calculated based on API documentation
            }
            
            response = requests.post(session_url, headers=self.headers, data=session_data)
            if response.status_code != 200:
                logger.error(f"Session token generation failed: {response.text}")
                return False
            
            session_response = response.json()
            if session_response["status"] != "success":
                logger.error(f"Session token generation failed: {session_response['message']}")
                return False
            
            # Save access token
            self.access_token = session_response["data"]["access_token"]
            
            # Update headers with authorization
            self.headers["Authorization"] = f"token {self.api_key}:{self.access_token}"
            
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get current positions.
        
        Returns:
            List of position objects or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/portfolio/positions"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get positions: {response.text}")
                return None
            
            positions_response = response.json()
            if positions_response["status"] != "success":
                logger.error(f"Failed to get positions: {positions_response['message']}")
                return None
            
            return positions_response["data"]["net"]
            
        except Exception as e:
            logger.error(f"Get positions error: {str(e)}")
            return None
    
    def get_option_chain_master(self) -> Optional[Dict[str, Any]]:
        """
        Get option chain master data.
        
        Returns:
            Option chain master data or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/getoptionchainmaster/2"  # 2 is for NSE
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get option chain master: {response.text}")
                return None
            
            master_response = response.json()
            if master_response["status"] != "success":
                logger.error(f"Failed to get option chain master: {master_response['message']}")
                return None
            
            return master_response["data"]
            
        except Exception as e:
            logger.error(f"Get option chain master error: {str(e)}")
            return None
    
    def get_option_chain(self, expiry_timestamp: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get option chain data for a specific expiry and token.
        
        Args:
            expiry_timestamp: Expiry timestamp
            token: Instrument token
            
        Returns:
            Option chain data or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/GetOptionChain/2/{expiry_timestamp}/{token}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get option chain: {response.text}")
                return None
            
            chain_response = response.json()
            if chain_response["status"] != "success":
                logger.error(f"Failed to get option chain: {chain_response['message']}")
                return None
            
            return chain_response["data"]
            
        except Exception as e:
            logger.error(f"Get option chain error: {str(e)}")
            return None
    
    def place_order(self, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Place an order.
        
        Args:
            order_params: Order parameters
            
        Returns:
            Order response or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/order/place"
            response = requests.post(url, headers=self.headers, data=order_params)
            
            if response.status_code != 200:
                logger.error(f"Failed to place order: {response.text}")
                return None
            
            order_response = response.json()
            if order_response["status"] != "success":
                logger.error(f"Failed to place order: {order_response['message']}")
                return None
            
            return order_response["data"]
            
        except Exception as e:
            logger.error(f"Place order error: {str(e)}")
            return None
    
    def modify_order(self, order_id: str, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            order_params: New order parameters
            
        Returns:
            Order response or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/order/modify"
            order_params["order_id"] = order_id
            
            response = requests.post(url, headers=self.headers, data=order_params)
            
            if response.status_code != 200:
                logger.error(f"Failed to modify order: {response.text}")
                return None
            
            modify_response = response.json()
            if modify_response["status"] != "success":
                logger.error(f"Failed to modify order: {modify_response['message']}")
                return None
            
            return modify_response["data"]
            
        except Exception as e:
            logger.error(f"Modify order error: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            url = f"{self.base_url}/openapi/typea/order/cancel"
            data = {"order_id": order_id}
            
            response = requests.post(url, headers=self.headers, data=data)
            
            if response.status_code != 200:
                logger.error(f"Failed to cancel order: {response.text}")
                return False
            
            cancel_response = response.json()
            if cancel_response["status"] != "success":
                logger.error(f"Failed to cancel order: {cancel_response['message']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Cancel order error: {str(e)}")
            return False
    
    def get_order_history(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get order history.
        
        Returns:
            List of orders or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/order/history"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get order history: {response.text}")
                return None
            
            history_response = response.json()
            if history_response["status"] != "success":
                logger.error(f"Failed to get order history: {history_response['message']}")
                return None
            
            return history_response["data"]
            
        except Exception as e:
            logger.error(f"Get order history error: {str(e)}")
            return None
    
    def get_fund_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get fund summary.
        
        Returns:
            Fund summary or None if request fails
        """
        try:
            url = f"{self.base_url}/openapi/typea/fund/summary"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get fund summary: {response.text}")
                return None
            
            fund_response = response.json()
            if fund_response["status"] != "success":
                logger.error(f"Failed to get fund summary: {fund_response['message']}")
                return None
            
            return fund_response["data"]
            
        except Exception as e:
            logger.error(f"Get fund summary error: {str(e)}")
            return None
