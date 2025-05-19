"""
Test script to run all tests for the trading application.
"""

import unittest
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logging


def run_tests():
    """
    Run all tests and return True if all pass, False otherwise.
    """
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting test execution...")
    
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests')
    test_suite = test_loader.discover(test_dir, pattern='test_*.py')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Log test results
    if result.wasSuccessful():
        logger.info(f"All tests passed! ({result.testsRun} tests run)")
    else:
        logger.error(f"Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        for failure in result.failures:
            logger.error(f"Failure in {failure[0]}: {failure[1]}")
        for error in result.errors:
            logger.error(f"Error in {error[0]}: {error[1]}")
    
    # Return True if all tests pass
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
