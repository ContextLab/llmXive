"""
Error handling utilities for the pipeline.
Implements safe wrappers for memory and download errors.
"""
import logging
import sys
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps
from exceptions import DownloadError, MemoryErrorHandled, ValidationError
from logging_config import get_logger, log_event

logger = get_logger("error_handling")

T = TypeVar('T')

def handle_download_failure(func: Callable) -> Callable:
    """Decorator to handle download errors specifically."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Download failed in {func.__name__}: {str(e)}")
            # Raise a specific DownloadError to be caught by the pipeline
            raise DownloadError(f"Download failed: {str(e)}") from e
    return wrapper

def handle_memory_error(e: Exception, context: str = "") -> None:
    """
    Handle memory errors by logging and raising a custom exception.
    This ensures the pipeline fails loudly rather than returning synthetic data.
    """
    logger.critical(f"Memory error in {context}: {str(e)}")
    raise MemoryErrorHandled(f"Memory limit exceeded in {context}: {str(e)}") from e

def safe_download(func: Callable) -> Callable:
    """Decorator to safely download data, handling network and memory issues."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except MemoryError as e:
            handle_memory_error(e, func.__name__)
        except Exception as e:
            raise DownloadError(f"Safe download failed: {str(e)}") from e
    return wrapper

def safe_process_item(func: Callable) -> Callable:
    """
    Decorator to safely process individual items (e.g., CIF files).
    Catches exceptions and returns a failure status instead of crashing the whole batch.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except MemoryError as e:
            handle_memory_error(e, func.__name__)
        except Exception as e:
            # Log but do not crash the batch for individual item failures
            logger.warning(f"Item processing failed in {func.__name__}: {str(e)}")
            return {"error": str(e), "success": False}
    return wrapper

def main():
    """Placeholder for error handling module tests."""
    pass

if __name__ == "__main__":
    main()
