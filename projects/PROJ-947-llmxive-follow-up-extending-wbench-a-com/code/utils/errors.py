"""
Error handling utilities for the llmXive pipeline.

This module provides strict error handling wrappers that enforce the project's
"fail loudly, never silently" policy. It explicitly forbids synthetic fallbacks
or silent suppression of errors.
"""

import logging
import sys
from functools import wraps
from typing import Callable, Optional, Any

# Import the logger factory from the existing logging module
from utils.logging import get_logger, log_error, log_exception

# Define custom exceptions for specific pipeline failure modes
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class ConvergenceError(PipelineError):
    """Raised when an iterative algorithm fails to converge."""
    pass

class DataValidationError(PipelineError):
    """Raised when data fails validation checks."""
    pass

class ResourceLimitError(PipelineError):
    """Raised when resource limits (RAM, time) are exceeded."""
    pass

class SyntheticFallbackForbiddenError(PipelineError):
    """
    Raised when code attempts to fall back to synthetic data or mock values
    instead of failing loudly on a real data source failure.
    """
    pass


def fail_loudly(message: str, error_type: type = PipelineError, **kwargs) -> None:
    """
    Log a critical error and raise an exception immediately.

    This function enforces the "fail loudly" policy. It logs the error with
    full context using the structured logging system and then raises an
    exception to halt execution. It explicitly forbids silent failures or
    synthetic fallbacks.

    Args:
        message: Human-readable error message.
        error_type: Exception class to raise. Defaults to PipelineError.
        **kwargs: Additional context to include in the log and exception.

    Raises:
        The specified exception_type with the provided message and context.
    """
    logger = get_logger(__name__)
    context = {
        "error_type": error_type.__name__,
        "message": message,
        **kwargs
    }

    # Log the error using the structured logging utility
    log_error(logger, message, extra_context=context)

    # Construct the full error message
    full_message = f"{error_type.__name__}: {message}"
    if kwargs:
        full_message += f" | Context: {kwargs}"

    # Raise the exception immediately - no fallback, no return
    raise error_type(full_message)


def skip_on_error(
    default_return: Optional[Any] = None,
    error_type: type = PipelineError,
    log_warning: bool = True
) -> Callable:
    """
    Decorator that catches specific errors, logs them, and optionally returns a default.

    WARNING: This function is STRICTLY for non-critical, optional operations.
    It must NEVER be used for:
    - Data loading from real sources
    - Core algorithm execution
    - Any operation where a silent failure would compromise result integrity

    If a real data fetch fails, it MUST raise (via fail_loudly), not skip.
    This decorator is only for things like:
    - Optional metadata fetching
    - Non-critical logging of side effects
    - Graceful degradation of non-essential features

    Args:
        default_return: Value to return if an error occurs. If None, re-raises.
        error_type: Exception type to catch.
        log_warning: If True, log a warning instead of an error.

    Returns:
        Decorated function.

    Raises:
        SyntheticFallbackForbiddenError: If used in a context where fallback is forbidden.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = get_logger(func.__module__)

                # Check if this is a synthetic fallback attempt
                if isinstance(e, SyntheticFallbackForbiddenError):
                    # Re-raise immediately - never allow synthetic fallback
                    log_error(logger, f"Synthetic fallback attempt detected in {func.__name__}", extra_context={"exception": str(e)})
                    raise

                if log_warning:
                    log_warning(logger, f"Skipping {func.__name__} due to error: {str(e)}", extra_context={"exception_type": type(e).__name__})
                else:
                    log_error(logger, f"Skipping {func.__name__} due to error: {str(e)}", extra_context={"exception_type": type(e).__name__})

                if default_return is not None:
                    return default_return
                else:
                    # If no default is provided, re-raise the error
                    raise

        return wrapper
    return decorator


def assert_no_synthetic_fallback(condition: bool, context: str = "") -> None:
    """
    Explicitly enforce that a condition is True, raising an error if it implies
    a synthetic fallback is being used.

    Args:
        condition: Must be True. If False, raises SyntheticFallbackForbiddenError.
        context: Additional context about what was being checked.

    Raises:
        SyntheticFallbackForbiddenError: If condition is False.
    """
    if not condition:
        msg = f"Synthetic fallback detected or implied. {context}"
        fail_loudly(msg, error_type=SyntheticFallbackForbiddenError)