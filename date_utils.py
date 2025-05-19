"""
Date utility functions for the trading application.
"""

import datetime
from typing import List, Optional, Tuple
import calendar

from config.config import HOLIDAYS


def is_market_holiday(date: datetime.date) -> bool:
    """
    Check if a given date is a market holiday.
    
    Args:
        date: Date to check
        
    Returns:
        True if holiday, False otherwise
    """
    date_str = date.strftime("%Y-%m-%d")
    return date_str in HOLIDAYS


def is_weekend(date: datetime.date) -> bool:
    """
    Check if a given date is a weekend.
    
    Args:
        date: Date to check
        
    Returns:
        True if weekend, False otherwise
    """
    return date.weekday() >= 5  # 5 is Saturday, 6 is Sunday


def is_trading_day(date: datetime.date) -> bool:
    """
    Check if a given date is a trading day (not a weekend or holiday).
    
    Args:
        date: Date to check
        
    Returns:
        True if trading day, False otherwise
    """
    return not (is_weekend(date) or is_market_holiday(date))


def get_next_trading_day(date: datetime.date) -> datetime.date:
    """
    Get the next trading day after a given date.
    
    Args:
        date: Starting date
        
    Returns:
        Next trading day
    """
    next_day = date + datetime.timedelta(days=1)
    while not is_trading_day(next_day):
        next_day += datetime.timedelta(days=1)
    return next_day


def get_previous_trading_day(date: datetime.date) -> datetime.date:
    """
    Get the previous trading day before a given date.
    
    Args:
        date: Starting date
        
    Returns:
        Previous trading day
    """
    prev_day = date - datetime.timedelta(days=1)
    while not is_trading_day(prev_day):
        prev_day -= datetime.timedelta(days=1)
    return prev_day


def get_next_expiry_date(from_date: datetime.date = None) -> datetime.date:
    """
    Get the next weekly expiry date (usually Thursday).
    
    Args:
        from_date: Starting date, defaults to today
        
    Returns:
        Next expiry date
    """
    if from_date is None:
        from_date = datetime.date.today()
    
    # Find the next Thursday (weekday 3)
    days_ahead = (3 - from_date.weekday()) % 7
    next_thursday = from_date + datetime.timedelta(days=days_ahead)
    
    # If today is Thursday and we're looking for the next expiry, go to next week
    if days_ahead == 0 and datetime.datetime.now().time() > datetime.time(15, 30):
        next_thursday += datetime.timedelta(days=7)
    
    # Check if it's a holiday, if so, move to the previous trading day
    while not is_trading_day(next_thursday):
        next_thursday = get_previous_trading_day(next_thursday)
    
    return next_thursday


def get_monthly_expiry_date(year: int, month: int) -> datetime.date:
    """
    Get the monthly expiry date (last Thursday of the month).
    
    Args:
        year: Year
        month: Month
        
    Returns:
        Monthly expiry date
    """
    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime.date(year, month, last_day)
    
    # Find the last Thursday of the month
    offset = (3 - last_date.weekday()) % 7
    last_thursday = last_date - datetime.timedelta(days=(7 - offset) % 7)
    
    # Check if it's a holiday, if so, move to the previous trading day
    while not is_trading_day(last_thursday):
        last_thursday = get_previous_trading_day(last_thursday)
    
    return last_thursday


def get_expiry_dates(weeks_ahead: int, from_date: datetime.date = None) -> List[datetime.date]:
    """
    Get a list of expiry dates for a specified number of weeks ahead.
    
    Args:
        weeks_ahead: Number of weeks ahead to get expiry dates for
        from_date: Starting date, defaults to today
        
    Returns:
        List of expiry dates
    """
    if from_date is None:
        from_date = datetime.date.today()
    
    expiry_dates = []
    current_date = from_date
    
    for _ in range(weeks_ahead):
        next_expiry = get_next_expiry_date(current_date)
        expiry_dates.append(next_expiry)
        current_date = next_expiry + datetime.timedelta(days=1)
    
    return expiry_dates


def get_expiry_date_n_weeks_ahead(n: int, from_date: datetime.date = None) -> datetime.date:
    """
    Get the expiry date n weeks ahead.
    
    Args:
        n: Number of weeks ahead
        from_date: Starting date, defaults to today
        
    Returns:
        Expiry date n weeks ahead
    """
    expiry_dates = get_expiry_dates(n, from_date)
    return expiry_dates[-1] if expiry_dates else None


def timestamp_to_datetime(timestamp: int) -> datetime.datetime:
    """
    Convert a Unix timestamp to a datetime object.
    
    Args:
        timestamp: Unix timestamp in seconds
        
    Returns:
        Datetime object
    """
    return datetime.datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime.datetime) -> int:
    """
    Convert a datetime object to a Unix timestamp.
    
    Args:
        dt: Datetime object
        
    Returns:
        Unix timestamp in seconds
    """
    return int(dt.timestamp())
