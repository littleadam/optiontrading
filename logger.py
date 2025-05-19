"""
Logging configuration for the trading application.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

from config.config import LOGGING_CONFIG


def setup_logging() -> Dict[str, Any]:
    """
    Set up logging for the application.
    
    Returns:
        Dictionary with logger objects
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOGGING_CONFIG["log_level"]))
    
    # Configure formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure main log file handler
    log_file = os.path.join(logs_dir, LOGGING_CONFIG["log_file"])
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Configure error log file handler
    error_log_file = os.path.join(logs_dir, LOGGING_CONFIG["error_log_file"])
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)
    
    # Create logger dictionary
    loggers = {
        "root": root_logger,
        "console": console_handler,
        "file": file_handler,
        "error_file": error_file_handler
    }
    
    return loggers


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger object
    """
    return logging.getLogger(name)
