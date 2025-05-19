"""
Short Strangle strategy implementation for Nifty 50.
"""

import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple
import time

from src.api.mstock_api import MStockAPI
from src.models.order import Order, OrderType, OrderSide, OrderStatus, ProductType, OptionType
from src.models.position import Position
from src.models.option_chain import OptionChain, OptionContract
from src.utils.date_utils import get_expiry_date_n_weeks_ahead, is_trading_day, get_next_trading_day
from src.utils.option_utils import (
    calculate_lot_size, find_strike_prices_for_strangle, find_option_contract,
    calculate_hedge_strike, is_premium_target_met, should_trigger_stop_loss,
    should_trigger_martingale, calculate_position_value, calculate_position_pnl
)
from config.config import STRATEGY_CONFIG, INVESTMENT_CONFIG, TRADING_HOURS


logger = logging.getLogger(__name__)


class ShortStrangleStrategy:
    """
    Implementation of the Short Strangle strategy for Nifty 50.
    """
    
    def __init__(self, api: MStockAPI):
        """
        Initialize the strategy.
        
        Args:
            api: MStockAPI client
        """
        self.api = api
        self.active_orders = {}  # Order ID -> Order
        self.active_positions = {}  # Symbol -> Position
        self.placed_orders_cache = set()  # Set of (symbol, strike, option_type, is_hedge, is_martingale) tuples
        
    def initialize(self) -> bool:
        """
        Initialize the strategy by logging in and fetching initial data.
        
        Returns:
            True if initialization successful, False otherwise
        """
        # Login to API
        if not self.api.login():
            logger.error("Failed to login to API")
            return False
        
        # Fetch current positions
        positions = self.api.get_positions()
        if positions is None:
            logger.error("Failed to fetch positions")
            return False
        
        # Update active positions
        for position_data in positions:
            position = Position.from_api_response(position_data)
            self.active_positions[position.symbol] = position
        
        logger.info(f"Initialized strategy with {len(self.active_positions)} active positions")
        return True
    
    def calculate_investment_amount(self) -> float:
        """
        Calculate the total investment amount based on fund summary.
        
        Returns:
            Total investment amount
        """
        fund_summary = self.api.get_fund_summary()
        if fund_summary is None:
            logger.warning("Failed to fetch fund summary, using base investment amount")
            return INVESTMENT_CONFIG["base_investment"]
        
        # Extract invested amount and available funds
        invested_amount = float(fund_summary.get("invested_amount", 0))
        available_funds = float(fund_summary.get("available_funds", 0))
        
        total_investment = invested_amount + available_funds
        logger.info(f"Calculated total investment: {total_investment}")
        
        return total_investment
    
    def get_option_chain_for_expiry(self, expiry_date: datetime.date) -> Optional[OptionChain]:
        """
        Get option chain data for a specific expiry date.
        
        Args:
            expiry_date: Expiry date
            
        Returns:
            OptionChain object or None if request fails
        """
        # First get option chain master to find expiry timestamp and token
        master_data = self.api.get_option_chain_master()
        if master_data is None:
            logger.error("Failed to fetch option chain master")
            return None
        
        # Find NIFTY in the option chain master
        nifty_data = None
        for item in master_data.get("OPTIDX", []):
            if item.startswith("NIFTY,"):
                nifty_data = item
                break
        
        if nifty_data is None:
            logger.error("Failed to find NIFTY in option chain master")
            return None
        
        # Parse NIFTY data to get token
        nifty_parts = nifty_data.split(",")
        if len(nifty_parts) < 2:
            logger.error("Invalid NIFTY data format in option chain master")
            return None
        
        token = nifty_parts[1]
        
        # Find expiry timestamp that matches our expiry date
        expiry_timestamp = None
        for exp_id, timestamp in master_data.get("dctExp", {}).items():
            exp_date = datetime.datetime.fromtimestamp(timestamp).date()
            if exp_date == expiry_date:
                expiry_timestamp = timestamp
                break
        
        if expiry_timestamp is None:
            logger.error(f"Failed to find expiry timestamp for date {expiry_date}")
            return None
        
        # Get option chain data
        chain_data = self.api.get_option_chain(str(expiry_timestamp), token)
        if chain_data is None:
            logger.error("Failed to fetch option chain data")
            return None
        
        # Convert to OptionChain object
        expiry_datetime = datetime.datetime.combine(expiry_date, datetime.time(15, 30))
        return OptionChain.from_api_response(chain_data, expiry_datetime)
    
    def place_short_strangle(self, investment_amount: float) -> bool:
        """
        Place a short strangle position.
        
        Args:
            investment_amount: Investment amount
            
        Returns:
            True if successful, False otherwise
        """
        # Calculate lot size
        lot_size = calculate_lot_size(investment_amount)
        quantity = lot_size * INVESTMENT_CONFIG["lot_size"]
        
        # Get expiry dates
        sell_expiry_date = get_expiry_date_n_weeks_ahead(STRATEGY_CONFIG["sell_expiry_weeks"])
        hedge_expiry_date = get_expiry_date_n_weeks_ahead(STRATEGY_CONFIG["hedge_expiry_weeks"])
        
        if sell_expiry_date is None or hedge_expiry_date is None:
            logger.error("Failed to calculate expiry dates")
            return False
        
        # Get option chains
        sell_chain = self.get_option_chain_for_expiry(sell_expiry_date)
        hedge_chain = self.get_option_chain_for_expiry(hedge_expiry_date)
        
        if sell_chain is None or hedge_chain is None:
            logger.error("Failed to fetch option chains")
            return False
        
        # Find strike prices for short strangle
        call_strike, put_strike = find_strike_prices_for_strangle(sell_chain)
        
        # Find option contracts
        sell_call = find_option_contract(sell_chain, call_strike, "CE")
        sell_put = find_option_contract(sell_chain, put_strike, "PE")
        
        if sell_call is None or sell_put is None:
            logger.error("Failed to find option contracts for short strangle")
            return False
        
        # Check if premium meets target
        call_premium = sell_call.last_price
        put_premium = sell_put.last_price
        
        if not (is_premium_target_met(call_premium * quantity, investment_amount) and 
                is_premium_target_met(put_premium * quantity, investment_amount)):
            logger.warning("Premium does not meet target percentage of investment")
            # Continue anyway, as this is just a warning
        
        # Calculate hedge strike prices
        hedge_call_strike = calculate_hedge_strike(call_strike, call_premium, "CE")
        hedge_put_strike = calculate_hedge_strike(put_strike, put_premium, "PE")
        
        # Find hedge option contracts
        hedge_call = find_option_contract(hedge_chain, hedge_call_strike, "CE")
        hedge_put = find_option_contract(hedge_chain, hedge_put_strike, "PE")
        
        if hedge_call is None or hedge_put is None:
            logger.error("Failed to find hedge option contracts")
            return False
        
        # Check if orders already placed
        call_key = (sell_call.symbol, call_strike, "CE", False, False)
        put_key = (sell_put.symbol, put_strike, "PE", False, False)
        hedge_call_key = (hedge_call.symbol, hedge_call_strike, "CE", True, False)
        hedge_put_key = (hedge_put.symbol, hedge_put_strike, "PE", True, False)
        
        if call_key in self.placed_orders_cache or put_key in self.placed_orders_cache:
            logger.info("Short strangle sell orders already placed")
            return True
        
        # Place sell orders
        sell_call_order = Order(
            symbol=sell_call.symbol,
            exchange="NFO",
            order_type=OrderType.MARKET,
            side=OrderSide.SELL,
            quantity=quantity,
            product=ProductType.NRML,
            option_type=OptionType.CE,
            strike_price=call_strike,
            expiry_date=datetime.datetime.combine(sell_expiry_date, datetime.time(15, 30))
        )
        
        sell_put_order = Order(
            symbol=sell_put.symbol,
            exchange="NFO",
            order_type=OrderType.MARKET,
            side=OrderSide.SELL,
            quantity=quantity,
            product=ProductType.NRML,
            option_type=OptionType.PE,
            strike_price=put_strike,
            expiry_date=datetime.datetime.combine(sell_expiry_date, datetime.time(15, 30))
        )
        
        # Place hedge buy orders
        hedge_call_order = Order(
            symbol=hedge_call.symbol,
            exchange="NFO",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=quantity,
            product=ProductType.NRML,
            option_type=OptionType.CE,
            strike_price=hedge_call_strike,
            expiry_date=datetime.datetime.combine(hedge_expiry_date, datetime.time(15, 30)),
            is_hedge=True
        )
        
        hedge_put_order = Order(
            symbol=hedge_put.symbol,
            exchange="NFO",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=quantity,
            product=ProductType.NRML,
            option_type=OptionType.PE,
            strike_price=hedge_put_strike,
            expiry_date=datetime.datetime.combine(hedge_expiry_date, datetime.time(15, 30)),
            is_hedge=True
        )
        
        # Execute orders
        orders = [sell_call_order, sell_put_order, hedge_call_order, hedge_put_order]
        success = True
        
        for order in orders:
            order_params = order.to_api_params()
            response = self.api.place_order(order_params)
            
            if response is None:
                logger.error(f"Failed to place order: {order.symbol}")
                success = False
                continue
            
            order.order_id = response.get("order_id")
            self.active_orders[order.order_id] = order
            
            # Add to placed orders cache
            key = (order.symbol, order.strike_price, order.option_type.value, order.is_hedge, order.is_martingale)
            self.placed_orders_cache.add(key)
            
            logger.info(f"Placed order: {order.side.value} {order.symbol} at {order.strike_price}")
        
        return success
    
    def handle_stop_loss(self, position: Position) -> bool:
        """
        Handle stop loss for a position.
        
        Args:
            position: Position to handle
            
        Returns:
            True if successful, False otherwise
        """
        # Check if stop loss should be triggered
        if not should_trigger_stop_loss(position.average_price, position.last_price):
            return True  # No action needed
        
        # Place stop loss order
        stop_loss_order = Order(
            symbol=position.symbol,
            exchange=position.exchange,
            order_type=OrderType.MARKET,
            side=OrderSide.BUY if position.quantity < 0 else OrderSide.SELL,  # Opposite of position
            quantity=abs(position.quantity),
            product=ProductType(position.product),
            option_type=position.option_type
        )
        
        order_params = stop_loss_order.to_api_params()
        response = self.api.place_order(order_params)
        
        if response is None:
            logger.error(f"Failed to place stop loss order for {position.symbol}")
            return False
        
        stop_loss_order.order_id = response.get("order_id")
        self.active_orders[stop_loss_order.order_id] = stop_loss_order
        
        logger.info(f"Placed stop loss order for {position.symbol}")
        
        # Place new sell order at same strike and expiry
        # This would require getting the option chain again to find the contract
        # For simplicity, we'll assume the same symbol can be used
        new_sell_order = Order(
            symbol=position.symbol,
            exchange=position.exchange,
            order_type=OrderType.MARKET,
            side=OrderSide.SELL if position.quantity < 0 else OrderSide.BUY,  # Same as original position
            quantity=abs(position.quantity),
            product=ProductType(position.product),
            option_type=position.option_type
        )
        
        order_params = new_sell_order.to_api_params()
        response = self.api.place_order(order_params)
        
        if response is None:
            logger.error(f"Failed to place new sell order for {position.symbol}")
            return False
        
        new_sell_order.order_id = response.get("order_id")
        self.active_orders[new_sell_order.order_id] = new_sell_order
        
        logger.info(f"Placed new sell order for {position.symbol}")
        
        return True
    
    def handle_martingale(self, position: Position) -> bool:
        """
        Handle martingale strategy for a position.
        
        Args:
            position: Position to handle
            
        Returns:
            True if successful, False otherwise
        """
        # Check if martingale should be triggered
        if not should_trigger_martingale(position.average_price, position.last_price):
            return True  # No action needed
        
        # Get option chain to find next strike
        # For simplicity, we'll assume we know the expiry date
        # In a real implementation, we would extract this from the position symbol
        expiry_date = position.expiry_date.date() if position.expiry_date else datetime.date.today()
        option_chain = self.get_option_chain_for_expiry(expiry_date)
        
        if option_chain is None:
            logger.error("Failed to fetch option chain for martingale")
            return False
        
        # Find next strike price
        option_type = position.option_type.value if position.option_type else "CE"
        current_strike = position.strike_price or 0
        
        # Find next strike in the appropriate direction
        if option_type == "CE":
            next_strikes = sorted([c.strike_price for c in option_chain.calls if c.strike_price > current_strike])
            next_strike = next_strikes[0] if next_strikes else current_strike + 100  # Default increment
        else:  # PE
            next_strikes = sorted([c.strike_price for c in option_chain.puts if c.strike_price < current_strike], reverse=True)
            next_strike = next_strikes[0] if next_strikes else current_strike - 100  # Default decrement
        
        # Find option contract for next strike
        next_contract = find_option_contract(option_chain, next_strike, option_type)
        
        if next_contract is None:
            logger.error(f"Failed to find option contract for next strike {next_strike}")
            return False
        
        # Place buy order for next strike
        buy_order = Order(
            symbol=next_contract.symbol,
            exchange="NFO",
            order_type=OrderType.MARKET,
      
(Content truncated due to size limit. Use line ranges to read in chunks)