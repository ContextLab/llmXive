"""
Error handling framework for the statistical discrepancies research pipeline.
Provides decorators and utility functions for robust error handling and validation.
"""
import traceback
import sys
from functools import wraps
from typing import Callable, Any, TypeVar, Optional, Dict, List
import logging
from .exceptions import (
    DiscrepancyError,
    DataAcquisitionError,
    MissingDataError,
    ValidationFailureError,
    StatisticalModelError,
    ConfigurationError,
    ReproducibilityError
)

# Get logger for this module
logger = logging.getLogger(__name__)


T = TypeVar('T')


def error_handler_factory(
    default_error: type = DiscrepancyError,
    log_level: int = logging.ERROR,
    re_raise: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Factory function to create error handling decorators.
    
    Args:
        default_error: Default exception type to raise if not specified.
        log_level: Logging level for error messages.
        re_raise: If True, re-raise the exception after logging; otherwise return None.
    
    Returns:
        A decorator function that wraps the target function with error handling.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except DiscrepancyError as e:
                logger.log(log_level, f"{func.__name__} failed with {type(e).__name__}: {e.message}", 
                           extra={"context": getattr(e, 'context', {})})
                if re_raise:
                    raise
                return None
            except Exception as e:
                # Log the full traceback for unexpected errors
                logger.exception(f"{func.__name__} failed with unexpected error: {str(e)}")
                error = default_error(f"Unexpected error in {func.__name__}: {str(e)}")
                if re_raise:
                    raise error from e
                return None
        return wrapper
    return decorator


def handle_errors(
    func: Callable[..., T],
    error_type: type = DiscrepancyError,
    message: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Callable[..., T]:
    """
    Decorator to handle errors in a function with a specific error type.
    
    Args:
        func: The function to wrap.
        error_type: The type of exception to raise on failure.
        message: Custom error message. If None, uses function name.
        context: Optional context to include in the error.
    
    Returns:
        Wrapped function with error handling.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = message or f"Error in {func.__name__}: {str(e)}"
            logger.error(error_message, extra={"context": context})
            raise error_type(error_message, context=context) from e
    return wrapper


def safe_execute(
    func: Callable[..., T],
    default_value: Optional[T] = None,
    catch_exceptions: Optional[List[type]] = None
) -> Callable[..., T]:
    """
    Decorator to safely execute a function, returning a default value on failure.
    
    Args:
        func: The function to wrap.
        default_value: Value to return if an exception occurs.
        catch_exceptions: List of exception types to catch. If None, catches all.
    
    Returns:
        Wrapped function that returns default_value on failure.
    """
    if catch_exceptions is None:
        catch_exceptions = [Exception]
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        try:
            return func(*args, **kwargs)
        except tuple(catch_exceptions) as e:
            logger.warning(f"Function {func.__name__} failed: {str(e)}. Returning default value.")
            return default_value
    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: List[str], context: Optional[str] = None) -> None:
    """
    Validate that all required fields are present in a dictionary.
    
    Args:
        data: Dictionary to validate.
        required_fields: List of field names that must be present.
        context: Optional context string for error messages.
    
    Raises:
        ValidationFailureError: If any required field is missing.
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        context_str = f" in {context}" if context else ""
        msg = f"Missing required fields{context_str}: {missing}"
        logger.error(msg)
        raise ValidationFailureError(msg, context={"missing_fields": missing, "data_keys": list(data.keys())})


def validate_input_types(
    data: Any,
    expected_type: type,
    field_name: Optional[str] = None
) -> None:
    """
    Validate that input data is of the expected type.
    
    Args:
        data: Data to validate.
        expected_type: Expected type.
        field_name: Optional name of the field for error messages.
    
    Raises:
        ValidationFailureError: If data is not of the expected type.
    """
    field_str = f" '{field_name}'" if field_name else ""
    if not isinstance(data, expected_type):
        msg = f"Input{field_str} must be of type {expected_type.__name__}, got {type(data).__name__}"
        logger.error(msg)
        raise ValidationFailureError(msg, context={"expected": expected_type.__name__, "actual": type(data).__name__})


def log_function_call(
    func: Callable[..., T]
) -> Callable[..., T]:
    """
    Decorator to log function entry and exit with arguments.
    
    Args:
        func: The function to wrap.
    
    Returns:
        Wrapped function with logging.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        logger.debug(f"Entering {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__} successfully")
            return result
        except Exception as e:
            logger.debug(f"Exiting {func.__name__} with error: {str(e)}")
            raise
    return wrapper
