"""
Error handling utilities for the crystal structure prediction pipeline.

This module provides explicit handlers for MemoryError and DownloadError
to ensure failures are caught and logged without silent synthetic fallbacks.
"""

import logging
import sys
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps

# Import custom exceptions from the project's exceptions module
# Note: Using absolute import style relative to the 'code' package root
try:
    from exceptions import DownloadError, MemoryErrorHandled, ValidationError
except ImportError:
    # Fallback for direct execution or different import context
    from ..exceptions import DownloadError, MemoryErrorHandled, ValidationError

from logging_config import get_logger, log_event

T = TypeVar('T')

logger = get_logger(__name__)


class DownloadError(Exception):
    """Custom exception for data download failures."""
    pass


class MemoryErrorHandled(Exception):
    """Custom exception raised when a MemoryError is caught and handled."""
    pass


class ValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value


def handle_download_failure(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to catch DownloadError and re-raise with context.

    Ensures that download failures are explicitly logged and propagated
    without synthetic fallbacks.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except DownloadError as e:
            log_event(logger, "ERROR", "Download failed", {"error": str(e)})
            logger.error(f"DownloadError caught in {func.__name__}: {e}")
            raise
        except Exception as e:
            # Wrap unexpected errors that might indicate a download issue
            log_event(logger, "ERROR", "Unexpected error during download", {"error": str(e)})
            raise DownloadError(f"Unexpected error during download: {e}") from e
    return wrapper


def handle_memory_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to catch MemoryError and raise a custom MemoryErrorHandled.

    This ensures memory issues are explicitly handled and logged,
    preventing silent failures or synthetic data generation.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except MemoryError as e:
            msg = f"MemoryError caught in {func.__name__}: {e}"
            logger.error(msg)
            log_event(logger, "ERROR", "MemoryError handled", {"function": func.__name__, "error": str(e)})
            raise MemoryErrorHandled(msg) from e
        except Exception as e:
            # Let other exceptions pass through unless they are memory-related
            raise
    return wrapper


def safe_download(download_func: Callable[..., T]) -> Callable[..., T]:
    """
    Wrapper for download functions to ensure explicit error handling.

    This is a convenience wrapper that combines logging and error raising
    for download operations.
    """
    @wraps(download_func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        logger.info(f"Starting download: {download_func.__name__}")
        try:
            result = download_func(*args, **kwargs)
            logger.info(f"Download completed successfully: {download_func.__name__}")
            return result
        except DownloadError:
            raise
        except Exception as e:
            logger.error(f"Download failed with unexpected error: {e}")
            raise DownloadError(f"Download failed: {e}") from e
    return wrapper


def safe_process_item(process_func: Callable[..., T]) -> Callable[..., T]:
    """
    Wrapper for processing functions to handle MemoryError explicitly.

    Used for batch processing where individual items might cause memory issues.
    """
    @wraps(process_func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return process_func(*args, **kwargs)
        except MemoryError as e:
            logger.error(f"MemoryError in process_item: {e}")
            raise MemoryErrorHandled(f"MemoryError in {process_func.__name__}: {e}") from e
    return wrapper


def main() -> None:
    """
    Main entry point for testing error handlers directly.
    """
    logger.info("Testing error handlers...")

    # Test DownloadError handling
    @handle_download_failure
    def failing_download():
        raise DownloadError("Simulated download failure")

    try:
        failing_download()
    except DownloadError as e:
        logger.info(f"Caught expected DownloadError: {e}")

    # Test MemoryError handling
    @handle_memory_error
    def failing_memory():
        raise MemoryError("Simulated memory exhaustion")

    try:
        failing_memory()
    except MemoryErrorHandled as e:
        logger.info(f"Caught expected MemoryErrorHandled: {e}")

    logger.info("Error handler tests completed.")


if __name__ == "__main__":
    main()
