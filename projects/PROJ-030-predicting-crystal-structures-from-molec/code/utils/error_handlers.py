"""
Error handling utilities for the crystal structure prediction pipeline.

This module provides explicit handlers for MemoryError and DownloadError
to ensure failures are caught and logged without silent synthetic fallbacks.
It defines custom exceptions and decorators to wrap data processing and
download operations, ensuring that resource exhaustion or network failures
are propagated as explicit exceptions rather than returning synthetic data.
"""

import logging
import sys
from typing import Callable, Any, Optional, TypeVar, Dict
from functools import wraps

# Import custom exceptions from the project's exceptions module
# We use a try/except block to handle both package imports and direct script execution
try:
    from exceptions import DownloadError as BaseDownloadError
    from exceptions import MemoryErrorHandled as BaseMemoryErrorHandled
    from exceptions import ValidationError as BaseValidationError
except ImportError:
    # Fallback for when running as a script or in a different import context
    try:
        from ..exceptions import DownloadError as BaseDownloadError
        from ..exceptions import MemoryErrorHandled as BaseMemoryErrorHandled
        from ..exceptions import ValidationError as BaseValidationError
    except ImportError:
        # Fallback if exceptions module is not yet available (should not happen in normal flow)
        class BaseDownloadError(Exception):
            """Base DownloadError if module not found."""
            pass
        class BaseMemoryErrorHandled(Exception):
            """Base MemoryErrorHandled if module not found."""
            pass
        class BaseValidationError(Exception):
            """Base ValidationError if module not found."""
            pass

from logging_config import get_logger, log_event

T = TypeVar('T')

logger = get_logger(__name__)


# Re-export exceptions for convenience in other modules
# These are aliases to the ones defined in exceptions.py to ensure consistency
DownloadError = BaseDownloadError
MemoryErrorHandled = BaseMemoryErrorHandled
ValidationError = BaseValidationError


def handle_download_failure(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to catch DownloadError and re-raise with context.

    Ensures that download failures are explicitly logged and propagated
    without synthetic fallbacks. If a DownloadError occurs, it is logged
    and re-raised. Any other exception during download is wrapped in a
    DownloadError.

    Args:
        func: The download function to wrap.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except DownloadError as e:
            log_event(logger, "ERROR", "Download failed", {"error": str(e), "function": func.__name__})
            logger.error(f"DownloadError caught in {func.__name__}: {e}")
            raise
        except Exception as e:
            # Wrap unexpected errors that might indicate a download issue
            log_event(logger, "ERROR", "Unexpected error during download", {"error": str(e), "function": func.__name__})
            raise DownloadError(f"Unexpected error during download: {e}") from e
    return wrapper


def handle_memory_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to catch MemoryError and raise a custom MemoryErrorHandled.

    This ensures memory issues are explicitly handled and logged,
    preventing silent failures or synthetic data generation. When a
    MemoryError is caught, it is logged and re-raised as a
    MemoryErrorHandled exception.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except MemoryError as e:
            msg = f"MemoryError caught in {func.__name__}: {e}"
            logger.error(msg)
            log_event(logger, "ERROR", "MemoryError handled", {
                "function": func.__name__,
                "error": str(e)
            })
            raise MemoryErrorHandled(msg) from e
        except Exception as e:
            # Let other exceptions pass through unless they are memory-related
            raise
    return wrapper


def safe_download(download_func: Callable[..., T]) -> Callable[..., T]:
    """
    Wrapper for download functions to ensure explicit error handling.

    This is a convenience wrapper that combines logging and error raising
    for download operations. It logs the start and completion of the
    download and ensures DownloadError is raised on failure.

    Args:
        download_func: The download function to wrap.

    Returns:
        The wrapped function.
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
    If a MemoryError occurs, it is logged and raised as MemoryErrorHandled.

    Args:
        process_func: The processing function to wrap.

    Returns:
        The wrapped function.
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
    This function demonstrates the behavior of the decorators with simulated errors.
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
