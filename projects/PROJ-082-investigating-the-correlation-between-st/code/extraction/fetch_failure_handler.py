"""
Fetch Failure Handler for llmXive pipeline.

This module provides strict error handling for data fetching operations.
It ensures that any failure to fetch real data (network errors, 404s,
unreachable URLs) results in an immediate exception being raised.

CRITICAL CONSTRAINT: This module MUST NOT contain any fallback logic
that generates synthetic data, mocks data, or returns placeholder values
when a real fetch fails. All failures must be loud and explicit.
"""

import logging
import socket
from pathlib import Path
from typing import Callable, TypeVar, Any, Optional
from urllib.error import URLError, HTTPError
import requests

from utils.logger import get_logger, log_error_context

# Define a generic type for the fetch function
T = TypeVar('T')

# Custom exception for fetch failures
class FetchFailureError(Exception):
    """
    Raised when a real data fetch fails due to network issues,
    missing resources, or unreachable URLs.
    
    This exception is designed to fail loudly, preventing any
    silent fallback to synthetic or mock data.
    """
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)
        
        if original_exception:
            self.message += f" (Original error: {type(original_exception).__name__}: {str(original_exception)})"


def fetch_with_strict_failure(
    fetch_func: Callable[[], T],
    data_source_name: str,
    logger: Optional[logging.Logger] = None
) -> T:
    """
    Execute a fetch function with strict failure handling.
    
    This wrapper ensures that any exception raised during the fetch
    operation is caught, logged as a critical error, and re-raised
    as a FetchFailureError. It explicitly prevents any fallback
    to synthetic data generation.
    
    Args:
        fetch_func: A callable that performs the actual data fetch.
                   Should raise an exception on failure.
        data_source_name: Human-readable name of the data source
                         for logging purposes.
        logger: Optional logger instance. If None, a default logger
               will be created.
    
    Returns:
        The fetched data if successful.
    
    Raises:
        FetchFailureError: If the fetch function raises any exception.
        FetchFailureError: If the fetch function returns a placeholder
                          or synthetic data indicator (checked post-fetch).
    
    Examples:
        >>> def fetch_real_data():
        ...     # This would fetch from a real URL
        ...     response = requests.get("https://example.com/data.csv")
        ...     response.raise_for_status()
        ...     return response.text
        ...
        >>> data = fetch_with_strict_failure(fetch_real_data, "Study Data")
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Attempting to fetch real data from: {data_source_name}")
    
    try:
        result = fetch_func()
        
        # Post-fetch validation: Check if result looks like synthetic/fake data
        # This is a safeguard against accidentally returning mock data
        if result is None:
            raise FetchFailureError(
                f"Fetch returned None for {data_source_name}. "
                "Real data fetch failed silently."
            )
        
        if isinstance(result, str):
            # Check for common synthetic data markers
            synthetic_markers = [
                "synthetic", "mock", "fake", "placeholder", "sample_data",
                "generated_at", "not_real", "test_data"
            ]
            result_lower = result.lower()
            if any(marker in result_lower for marker in synthetic_markers):
                raise FetchFailureError(
                    f"Fetch returned synthetic/mock data for {data_source_name}. "
                    "Real data source is unavailable or misconfigured."
                )
        
        logger.info(f"Successfully fetched real data from: {data_source_name}")
        return result
        
    except (URLError, HTTPError, socket.gaierror, ConnectionError, 
            requests.exceptions.RequestException) as e:
        # Network-level failures
        error_msg = f"Network error while fetching {data_source_name}: {str(e)}"
        log_error_context(logger, error_msg, exc_info=True)
        raise FetchFailureError(error_msg, original_exception=e)
        
    except Exception as e:
        # Any other exception during fetch
        error_msg = f"Unexpected error while fetching {data_source_name}: {str(e)}"
        log_error_context(logger, error_msg, exc_info=True)
        raise FetchFailureError(error_msg, original_exception=e)


def validate_data_integrity(
    data: Any,
    expected_min_size: int = 0,
    data_source_name: str = "Unknown"
) -> bool:
    """
    Validate that fetched data meets minimum integrity requirements.
    
    This function ensures that the fetched data is not empty, truncated,
    or obviously invalid. It raises FetchFailureError if validation fails.
    
    Args:
        data: The fetched data to validate.
        expected_min_size: Minimum expected size (in bytes or elements).
        data_source_name: Name of the data source for error messages.
    
    Returns:
        True if data passes validation.
    
    Raises:
        FetchFailureError: If data validation fails.
    """
    if data is None:
        raise FetchFailureError(
            f"Data validation failed for {data_source_name}: Data is None"
        )
    
    if isinstance(data, (str, bytes, list, dict, tuple)):
        actual_size = len(data)
        if actual_size < expected_min_size:
            raise FetchFailureError(
                f"Data validation failed for {data_source_name}: "
                f"Size {actual_size} is less than required minimum {expected_min_size}. "
                "Real data fetch may have been incomplete."
            )
    
    logger = get_logger(__name__)
    logger.info(f"Data validation passed for {data_source_name}")
    return True


def main():
    """
    Main entry point for testing the fetch failure handler.
    
    This function demonstrates the strict failure behavior by attempting
    to fetch from a known unreachable URL. It should raise a FetchFailureError
    and NOT fall back to any synthetic data.
    """
    logger = get_logger(__name__)
    logger.info("=== Fetch Failure Handler Test ===")
    logger.info("This test will attempt to fetch from an unreachable URL")
    logger.info("Expected behavior: FetchFailureError raised, NO synthetic fallback")
    
    def simulate_unreachable_fetch():
        """Simulate a fetch that will fail."""
        try:
            # Try to fetch from a non-existent domain
            response = requests.get("http://this-domain-definitely-does-not-exist-12345.com/data.csv", timeout=5)
            response.raise_for_status()
            return response.text
        except Exception as e:
            # Re-raise to be caught by the wrapper
            raise e
    
    try:
        result = fetch_with_strict_failure(
            simulate_unreachable_fetch,
            "Test Unreachable URL",
            logger
        )
        logger.error("ERROR: Fetch succeeded when it should have failed!")
        logger.error("This indicates the strict failure handler is not working correctly.")
        return False
        
    except FetchFailureError as e:
        logger.info(f"SUCCESS: FetchFailureError raised as expected: {e.message}")
        logger.info("No synthetic data fallback occurred.")
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Unexpected exception type: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
    exit(0)
