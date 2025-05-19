"""
Position model for representing and managing trading positions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import datetime

from src.models.order import OptionType


@dataclass
class Position:
    """
    Represents a trading position with all necessary attributes.
    """
    symbol: str
    exchange: str
    instrument_token: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float
    product: str
    option_type: Optional[OptionType] = None
    strike_price: Optional[float] = None
    expiry_date: Optional[datetime.datetime] = None
    buy_quantity: int = 0
    buy_price: float = 0.0
    buy_value: float = 0.0
    sell_quantity: int = 0
    sell_price: float = 0.0
    sell_value: float = 0.0
    day_buy_quantity: int = 0
    day_buy_price: float = 0.0
    day_buy_value: float = 0.0
    day_sell_quantity: int = 0
    day_sell_price: float = 0.0
    day_sell_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Position':
        """
        Create a Position object from API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            Position object
        """
        # Extract option details from symbol if available
        option_type = None
        strike_price = None
        expiry_date = None
        
        symbol = response.get("tradingsymbol", "")
        if "CE" in symbol:
            option_type = OptionType.CE
        elif "PE" in symbol:
            option_type = OptionType.PE
            
        # In a real implementation, we would parse the strike price and expiry date from the symbol
        # This is a simplified example
        
        return cls(
            symbol=symbol,
            exchange=response.get("exchange", ""),
            instrument_token=response.get("instrument_token", ""),
            quantity=int(response.get("quantity", 0)),
            average_price=float(response.get("average_price", 0)),
            last_price=float(response.get("last_price", 0)),
            pnl=float(response.get("pnl", 0)),
            product=response.get("product", ""),
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            buy_quantity=int(response.get("buy_quantity", 0)),
            buy_price=float(response.get("buy_price", 0)),
            buy_value=float(response.get("buy_value", 0)),
            sell_quantity=int(response.get("sell_quantity", 0)),
            sell_price=float(response.get("sell_price", 0)),
            sell_value=float(response.get("sell_value", 0)),
            day_buy_quantity=int(response.get("day_buy_quantity", 0)),
            day_buy_price=float(response.get("day_buy_price", 0)),
            day_buy_value=float(response.get("day_buy_value", 0)),
            day_sell_quantity=int(response.get("day_sell_quantity", 0)),
            day_sell_price=float(response.get("day_sell_price", 0)),
            day_sell_value=float(response.get("day_sell_value", 0)),
            unrealized_pnl=float(response.get("unrealised", 0)),
            realized_pnl=float(response.get("realised", 0))
        )
