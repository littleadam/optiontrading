"""
Error handling utilities for the trading application.
"""

import logging
import time
import functools
import traceback
from typing import Callable, Any, Dict, Optional, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class RetryException(Exception):
    """Exception raised when a retry is needed."""
    pass

def retry(max_attempts: int = 3, delay: int = 2, backoff: int = 2, 
          exceptions: tuple = (Exception,), logger_func=None):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
        logger_func: Function to use for logging
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_func if logger_func else logger.warning
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        log(f"Function {func.__name__} failed after {max_attempts} attempts. Error: {str(e)}")
                        raise
                    
                    log(f"Retry {attempt}/{max_attempts} for {func.__name__} after error: {str(e)}. "
                        f"Retrying in {current_delay} seconds...")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None  # Should not reach here
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default_return=None, log_exception=True, **kwargs) -> Any:
    """
    Execute a function safely, catching and logging any exceptions.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        default_return: Value to return if an exception occurs
        log_exception: Whether to log the exception
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result or default_return if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_exception:
            logger.error(f"Error executing {func.__name__}: {str(e)}")
            logger.debug(f"Exception traceback: {traceback.format_exc()}")
        return default_return

def validate_api_response(response: Dict[str, Any], required_fields: List[str] = None) -> bool:
    """
    Validate an API response.
    
    Args:
        response: API response to validate
        required_fields: List of required fields in the response
        
    Returns:
        True if valid, False otherwise
    """
    if response is None:
        logger.error("API response is None")
        return False
    
    if not isinstance(response, dict):
        logger.error(f"API response is not a dictionary: {type(response)}")
        return False
    
    if "status" not in response:
        logger.error("API response missing 'status' field")
        return False
    
    if response["status"] != "success":
        error_msg = response.get("message", "Unknown error")
        error_type = response.get("error_type", "Unknown")
        logger.error(f"API error: {error_type} - {error_msg}")
        return False
    
    if required_fields:
        for field in required_fields:
            if field not in response.get("data", {}):
                logger.error(f"API response missing required field: {field}")
                return False
    
    return True

def guard_empty_instruments(instruments: List[Any]) -> bool:
    """
    Guard against empty instrument lists.
    
    Args:
        instruments: List of instruments to check
        
    Returns:
        True if not empty, False otherwise
    """
    if not instruments:
        logger.error("Empty instrument list")
        return False
    
    return True

def guard_bad_ltp(ltp: float) -> bool:
    """
    Guard against bad LTP (Last Traded Price) values.
    
    Args:
        ltp: LTP value to check
        
    Returns:
        True if valid, False otherwise
    """
    if ltp <= 0:
        logger.error(f"Invalid LTP value: {ltp}")
        return False
    
    return True

def log_critical_error(message: str, error: Exception = None) -> None:
    """
    Log a critical error.
    
    Args:
        message: Error message
        error: Exception object
    """
    if error:
        logger.critical(f"{message}: {str(error)}")
        logger.debug(f"Exception traceback: {traceback.format_exc()}")
    else:
        logger.critical(message)
