"""
Option chain model for representing option chain data.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import datetime


@dataclass
class OptionContract:
    """
    Represents an individual option contract in the option chain.
    """
    symbol: str
    strike_price: float
    expiry_date: datetime.datetime
    option_type: str  # CE or PE
    instrument_token: str
    last_price: float
    change: float
    open_interest: int
    volume: int
    bid_price: float
    bid_quantity: int
    ask_price: float
    ask_quantity: int
    underlying_price: float


@dataclass
class OptionChain:
    """
    Represents an option chain with calls and puts at various strike prices.
    """
    underlying: str
    spot_price: float
    expiry_date: datetime.datetime
    calls: List[OptionContract]
    puts: List[OptionContract]
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any], expiry_date: datetime.datetime) -> 'OptionChain':
        """
        Create an OptionChain object from API response.
        
        Args:
            response: API response dictionary
            expiry_date: Expiry date for the option chain
            
        Returns:
            OptionChain object
        """
        # This is a simplified implementation and would need to be adjusted based on actual API response
        calls = []
        puts = []
        underlying = ""
        spot_price = 0.0
        
        # Extract data from the response
        if "contractModel" in response:
            contract_model = response["contractModel"]
            underlying = contract_model.get("sym", "")
            spot_price = float(contract_model.get("spotPrice", 0))
            
            # Process call options
            if "ce" in contract_model:
                for ce_data in contract_model["ce"]:
                    calls.append(OptionContract(
                        symbol=ce_data.get("sym", ""),
                        strike_price=float(ce_data.get("strikePrice", 0)),
                        expiry_date=expiry_date,
                        option_type="CE",
                        instrument_token=ce_data.get("token", ""),
                        last_price=float(ce_data.get("lastPrice", 0)),
                        change=float(ce_data.get("change", 0)),
                        open_interest=int(ce_data.get("openInterest", 0)),
                        volume=int(ce_data.get("volume", 0)),
                        bid_price=float(ce_data.get("bidPrice", 0)),
                        bid_quantity=int(ce_data.get("bidQty", 0)),
                        ask_price=float(ce_data.get("askPrice", 0)),
                        ask_quantity=int(ce_data.get("askQty", 0)),
                        underlying_price=spot_price
                    ))
            
            # Process put options
            if "pe" in contract_model:
                for pe_data in contract_model["pe"]:
                    puts.append(OptionContract(
                        symbol=pe_data.get("sym", ""),
                        strike_price=float(pe_data.get("strikePrice", 0)),
                        expiry_date=expiry_date,
                        option_type="PE",
                        instrument_token=pe_data.get("token", ""),
                        last_price=float(pe_data.get("lastPrice", 0)),
                        change=float(pe_data.get("change", 0)),
                        open_interest=int(pe_data.get("openInterest", 0)),
                        volume=int(pe_data.get("volume", 0)),
                        bid_price=float(pe_data.get("bidPrice", 0)),
                        bid_quantity=int(pe_data.get("bidQty", 0)),
                        ask_price=float(pe_data.get("askPrice", 0)),
                        ask_quantity=int(pe_data.get("askQty", 0)),
                        underlying_price=spot_price
                    ))
        
        return cls(
            underlying=underlying,
            spot_price=spot_price,
            expiry_date=expiry_date,
            calls=calls,
            puts=puts
        )
