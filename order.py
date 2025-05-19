"""
Order model for representing and managing trading orders.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import datetime


class OrderType(Enum):
    """Order types supported by the trading system."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSide(Enum):
    """Order sides (buy/sell)."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Possible order statuses."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class ProductType(Enum):
    """Product types for orders."""
    CNC = "CNC"  # Cash and Carry
    NRML = "NRML"  # Normal (for F&O)
    MIS = "MIS"  # Margin Intraday Square-off


class OptionType(Enum):
    """Option types."""
    CE = "CE"  # Call Option
    PE = "PE"  # Put Option


@dataclass
class Order:
    """
    Represents a trading order with all necessary attributes.
    """
    symbol: str
    exchange: str
    order_type: OrderType
    side: OrderSide
    quantity: int
    price: float = 0.0  # For LIMIT orders
    trigger_price: float = 0.0  # For SL/SL-M orders
    product: ProductType = ProductType.NRML
    validity: str = "DAY"
    disclosed_quantity: int = 0
    order_id: Optional[str] = None
    parent_order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    placed_at: Optional[datetime.datetime] = None
    filled_at: Optional[datetime.datetime] = None
    average_price: float = 0.0
    filled_quantity: int = 0
    remaining_quantity: int = 0
    option_type: Optional[OptionType] = None
    strike_price: Optional[float] = None
    expiry_date: Optional[datetime.datetime] = None
    is_hedge: bool = False
    is_martingale: bool = False
    
    def to_api_params(self) -> Dict[str, Any]:
        """
        Convert order to API parameters for placing an order.
        
        Returns:
            Dict with API parameters
        """
        params = {
            "tradingsymbol": self.symbol,
            "exchange": self.exchange,
            "transaction_type": self.side.value,
            "order_type": self.order_type.value,
            "quantity": str(self.quantity),
            "product": self.product.value,
            "validity": self.validity,
        }
        
        if self.order_type == OrderType.LIMIT:
            params["price"] = str(self.price)
            
        if self.trigger_price > 0:
            params["trigger_price"] = str(self.trigger_price)
            
        if self.disclosed_quantity > 0:
            params["disclosed_quantity"] = str(self.disclosed_quantity)
            
        return params
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Order':
        """
        Create an Order object from API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            Order object
        """
        # Map API response fields to Order attributes
        # This is a simplified example and would need to be adjusted based on actual API response
        side = OrderSide.BUY if response.get("transaction_type") == "BUY" else OrderSide.SELL
        order_type = OrderType.MARKET if response.get("order_type") == "MARKET" else OrderType.LIMIT
        product = ProductType(response.get("product", "NRML"))
        
        status_map = {
            "OPEN": OrderStatus.OPEN,
            "COMPLETE": OrderStatus.COMPLETE,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "PENDING": OrderStatus.PENDING
        }
        status = status_map.get(response.get("status", "PENDING"), OrderStatus.PENDING)
        
        # Parse dates if available
        placed_at = None
        if "order_timestamp" in response:
            try:
                placed_at = datetime.datetime.fromisoformat(response["order_timestamp"])
            except (ValueError, TypeError):
                pass
                
        filled_at = None
        if "exchange_timestamp" in response:
            try:
                filled_at = datetime.datetime.fromisoformat(response["exchange_timestamp"])
            except (ValueError, TypeError):
                pass
        
        # Create and return the Order object
        return cls(
            symbol=response.get("tradingsymbol", ""),
            exchange=response.get("exchange", ""),
            order_type=order_type,
            side=side,
            quantity=int(response.get("quantity", 0)),
            price=float(response.get("price", 0)),
            trigger_price=float(response.get("trigger_price", 0)),
            product=product,
            validity=response.get("validity", "DAY"),
            disclosed_quantity=int(response.get("disclosed_quantity", 0)),
            order_id=response.get("order_id"),
            status=status,
            placed_at=placed_at,
            filled_at=filled_at,
            average_price=float(response.get("average_price", 0)),
            filled_quantity=int(response.get("filled_quantity", 0)),
            remaining_quantity=int(response.get("pending_quantity", 0))
        )
