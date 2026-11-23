"""
Centralized error handling utilities for the project.

This module provides consistent error handling patterns, custom exceptions,
and logging utilities used across the codebase.
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Any, Tuple
from functools import wraps

from utils.logging import get_logger, log_error

logger = get_logger(__name__)

class ProjectError(Exception):
    """Base exception for all project-specific errors."""
    pass

class ConfigurationError(ProjectError):
    """Error related to configuration issues."""
    pass

class DataError(ProjectError):
    """Error related to data loading or processing."""
    pass

class IntegrityError(DataError):
    """Error related to data integrity checks."""
    pass

class FetchError(DataError):
    """Error related to data fetching operations."""
    pass

class ProcessingError(DataError):
    """Error related to data processing operations."""
    pass

class ValidationError(ProjectError):
    """Error related to validation failures."""
    pass

def safe_execute(
    func: Callable, 
    *args, 
    default: Any = None, 
    log_errors: bool = True,
    exception_type: type = Exception
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        default: Default value to return on error
        log_errors: Whether to log the error
        exception_type: Type of exception to catch
        
    Returns:
        Tuple of (result, error_message)
    """
    try:
        result = func(*args)
        return result, None
    except exception_type as e:
        error_msg = str(e)
        if log_errors:
            logger.error(f"Error in {func.__name__}: {error_msg}")
            log_error(error_msg)
        return default, error_msg
    except Exception as e:
        error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
        if log_errors:
            logger.error(error_msg)
            log_error(error_msg)
        return default, error_msg

def validate_required_fields(data: dict, required_fields: list, context: str = "") -> None:
    """
    Validate that all required fields are present in a dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context string for error messages
        
    Raises:
        ValidationError: If any required field is missing
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        context_str = f" in {context}" if context else ""
        raise ValidationError(
            f"Missing required fields{context_str}: {', '.join(missing)}"
        )

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exception_type: type = Exception
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: Function to decorate
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exception_type: Type of exception to catch and retry
        
    Returns:
        Decorated function
    """
    import time
    import random
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        delay = base_delay
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    jitter = random.uniform(0, 0.1 * delay)
                    actual_delay = min(delay + jitter, max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )
                    time.sleep(actual_delay)
                    delay *= 2
        
        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
        raise last_exception
    
    return wrapper

def log_and_raise(func: Callable) -> Callable:
    """
    Decorator to log exceptions before re-raising them.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            log_error(error_msg)
            raise
    
    return wrapper