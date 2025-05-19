"""
Utility functions for option trading calculations.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import datetime

from src.models.option_chain import OptionContract, OptionChain
from config.config import STRATEGY_CONFIG


def calculate_lot_size(investment_amount: float) -> int:
    """
    Calculate the number of lots based on investment amount.
    
    Args:
        investment_amount: Total investment amount
        
    Returns:
        Number of lots
    """
    from config.config import INVESTMENT_CONFIG
    
    lots_per_investment = INVESTMENT_CONFIG["lots_per_investment"]
    investment_per_lot = INVESTMENT_CONFIG["investment_per_lot"]
    
    return math.floor(investment_amount / investment_per_lot) * lots_per_investment


def find_strike_prices_for_strangle(option_chain: OptionChain, distance: int = None) -> Tuple[float, float]:
    """
    Find appropriate strike prices for a short strangle based on spot price and distance.
    
    Args:
        option_chain: Option chain data
        distance: Minimum distance from spot price (points)
        
    Returns:
        Tuple of (call_strike, put_strike)
    """
    if distance is None:
        distance = STRATEGY_CONFIG["strangle_distance"]
    
    spot_price = option_chain.spot_price
    
    # Find call strike at least 'distance' points above spot price
    call_strikes = sorted([contract.strike_price for contract in option_chain.calls])
    put_strikes = sorted([contract.strike_price for contract in option_chain.puts], reverse=True)
    
    call_strike = next((strike for strike in call_strikes if strike >= spot_price + distance), call_strikes[-1])
    put_strike = next((strike for strike in put_strikes if strike <= spot_price - distance), put_strikes[-1])
    
    return call_strike, put_strike


def find_option_contract(option_chain: OptionChain, strike_price: float, option_type: str) -> Optional[OptionContract]:
    """
    Find an option contract with the specified strike price and type.
    
    Args:
        option_chain: Option chain data
        strike_price: Strike price to find
        option_type: Option type (CE or PE)
        
    Returns:
        OptionContract if found, None otherwise
    """
    contracts = option_chain.calls if option_type == "CE" else option_chain.puts
    
    for contract in contracts:
        if abs(contract.strike_price - strike_price) < 0.01:  # Allow for small floating point differences
            return contract
    
    return None


def calculate_hedge_strike(sell_strike: float, premium: float, option_type: str) -> float:
    """
    Calculate the hedge strike price based on sell strike and premium.
    
    Args:
        sell_strike: Strike price of the sell order
        premium: Premium of the sell order
        option_type: Option type (CE or PE)
        
    Returns:
        Hedge strike price
    """
    if option_type == "CE":
        return sell_strike + premium
    else:  # PE
        return sell_strike - premium


def calculate_premium_percentage(premium: float, investment: float) -> float:
    """
    Calculate premium as a percentage of investment.
    
    Args:
        premium: Option premium
        investment: Investment amount
        
    Returns:
        Premium percentage
    """
    return (premium / investment) * 100


def is_premium_target_met(premium: float, investment: float) -> bool:
    """
    Check if premium meets the target percentage of investment.
    
    Args:
        premium: Option premium
        investment: Investment amount
        
    Returns:
        True if target met, False otherwise
    """
    target_percentage = STRATEGY_CONFIG["leg_premium_target"] * 100
    actual_percentage = calculate_premium_percentage(premium, investment)
    
    return actual_percentage >= target_percentage


def calculate_position_value(positions: List[Dict[str, Any]]) -> float:
    """
    Calculate the total value of positions.
    
    Args:
        positions: List of position dictionaries
        
    Returns:
        Total position value
    """
    return sum(float(position.get("value", 0)) for position in positions)


def calculate_position_pnl(positions: List[Dict[str, Any]]) -> float:
    """
    Calculate the total P&L of positions.
    
    Args:
        positions: List of position dictionaries
        
    Returns:
        Total position P&L
    """
    return sum(float(position.get("pnl", 0)) for position in positions)


def should_trigger_stop_loss(avg_price: float, current_price: float) -> bool:
    """
    Determine if stop loss should be triggered based on price drop.
    
    Args:
        avg_price: Average price of the position
        current_price: Current market price
        
    Returns:
        True if stop loss should be triggered, False otherwise
    """
    if avg_price <= 0:
        return False
    
    price_drop_percentage = (avg_price - current_price) / avg_price
    return price_drop_percentage >= STRATEGY_CONFIG["stop_loss_trigger"]


def should_trigger_martingale(avg_price: float, current_price: float) -> bool:
    """
    Determine if martingale strategy should be triggered based on price increase.
    
    Args:
        avg_price: Average price of the position
        current_price: Current market price
        
    Returns:
        True if martingale should be triggered, False otherwise
    """
    if avg_price <= 0:
        return False
    
    price_increase_ratio = current_price / avg_price
    return price_increase_ratio >= STRATEGY_CONFIG["martingale_trigger"]
