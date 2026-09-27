"""
Error Handling Framework for the Crystal Structure Prediction Pipeline.

This module provides explicit handlers for MemoryError and DownloadError,
ensuring that the pipeline 'fails loudly' without falling back to synthetic data.

Key Principles:
1. DownloadError: Must be raised immediately on fetch failure. No synthetic fallback.
2. MemoryError: Caught to allow graceful degradation (e.g., skipping a large item)
   but logged explicitly. The pipeline continues, but the missing data is not faked.
"""

import logging
import sys
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps

# Import custom exceptions defined in exceptions.py
from exceptions import DownloadError, MemoryErrorHandled, ValidationError

# Import logging infrastructure
from logging_config import get_logger, log_event

# Type variable for generic decorators
T = TypeVar('T')

logger = get_logger(__name__)

def handle_download_failure(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to wrap download functions and explicitly catch network/remote errors.
    Converts generic exceptions into DownloadError to enforce 'fail loudly' behavior.
    
    If the download fails, this decorator raises DownloadError. It does NOT
    return synthetic data or a placeholder.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (ConnectionError, TimeoutError, OSError) as e:
            # Explicitly catch network-level failures
            source = kwargs.get('source') or args[0] if args else "unknown"
            logger.error(f"Download failed for {source}: {str(e)}")
            raise DownloadError(str(e), source=source) from e
        except Exception as e:
            # Catch any other unexpected error during download
            source = kwargs.get('source') or args[0] if args else "unknown"
            logger.error(f"Unexpected error during download from {source}: {str(e)}")
            raise DownloadError(f"Unexpected error: {str(e)}", source=source) from e
    return wrapper

def handle_memory_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to wrap processing functions that might trigger MemoryError.
    
    When a MemoryError occurs, this decorator logs the event, raises a
    custom MemoryErrorHandled exception, and allows the caller to decide
    whether to skip the item or abort.
    
    Crucially: It does NOT generate synthetic data to replace the missing item.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except MemoryError as e:
            # Log the memory constraint explicitly
            item_desc = kwargs.get('item_id') or args[0] if args else "unknown_item"
            error_msg = f"MemoryError encountered while processing {item_desc}"
            logger.warning(error_msg)
            
            # Raise custom exception to signal graceful handling
            raise MemoryErrorHandled(error_msg, context={"item": item_desc}) from e
    return wrapper

def safe_download(download_func: Callable, source: str, **kwargs) -> Optional[Any]:
    """
    Utility function to perform a download with explicit error handling.
    
    Returns the downloaded data if successful.
    Raises DownloadError if the download fails (no synthetic fallback).
    """
    try:
        logger.info(f"Initiating download from {source}")
        result = download_func(source=source, **kwargs)
        log_event("download_success", {"source": source, "size": len(str(result))})
        return result
    except DownloadError:
        # Re-raise to ensure the pipeline knows data is missing
        raise
    except Exception as e:
        logger.critical(f"Unhandled exception in safe_download for {source}: {e}")
        raise DownloadError(f"Unhandled error: {e}", source=source) from e

def safe_process_item(process_func: Callable, item: Any, item_id: str = None) -> Optional[Any]:
    """
    Utility function to process a single item with memory error handling.
    
    Returns the processed item if successful.
    Returns None if a MemoryErrorHandled exception occurs (item skipped).
    Raises other exceptions as-is.
    
    This function ensures that memory errors are caught and logged,
    allowing the pipeline to continue with other items without faking data.
    """
    try:
        result = process_func(item)
        return result
    except MemoryErrorHandled as e:
        # Log and skip this specific item
        logger.warning(f"Skipping item {item_id} due to memory constraints: {e}")
        return None
    except Exception as e:
        # Let other errors propagate
        logger.error(f"Error processing item {item_id}: {e}")
        raise

def main():
    """
    Entry point for testing the error handling framework.
    Demonstrates the behavior of handle_download_failure and handle_memory_error.
    """
    logger.info("Testing Error Handling Framework")
    
    # Test DownloadError
    @handle_download_failure
    def mock_download_fail(source: str):
        raise ConnectionError("Simulated network failure")
    
    try:
        mock_download_fail("https://fake-url.com")
    except DownloadError as e:
        logger.info(f"Caught expected DownloadError: {e}")
    
    # Test MemoryErrorHandled
    @handle_memory_error
    def mock_process_fail(item: dict):
        raise MemoryError("Simulated out of memory")
    
    try:
        mock_process_fail({"id": 1})
    except MemoryErrorHandled as e:
        logger.info(f"Caught expected MemoryErrorHandled: {e}")
    
    logger.info("Error handling tests completed successfully.")
