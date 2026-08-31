"""
Error handling framework for the statistical discrepancies analysis pipeline.

Provides decorators and utilities for consistent error handling, logging,
and validation across the codebase.
"""
import traceback
import sys
from functools import wraps
from typing import Callable, Any, TypeVar, Optional, Dict, List
import logging

# Import custom exceptions
from .exceptions import (
    DiscrepancyError,
    DataAcquisitionError,
    MissingDataError,
    ValidationFailureError,
    StatisticalModelError,
    ConfigurationError
)
# Import logger
from .logger import get_logger, log_with_context

# Type variable for generic function return
T = TypeVar('T')

# Mapping of exception types to log levels
EXCEPTION_LOG_LEVELS = {
    DiscrepancyError: logging.ERROR,
    DataAcquisitionError: logging.ERROR,
    MissingDataError: logging.WARNING,
    ValidationFailureError: logging.ERROR,
    StatisticalModelError: logging.ERROR,
    ConfigurationError: logging.CRITICAL,
    Exception: logging.ERROR,
}

def handle_errors(
    log_level: Optional[int] = None,
    reraise: bool = True,
    fallback: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to handle exceptions with consistent logging and optional fallback.
    
    Args:
        log_level: Override default log level for all exceptions
        reraise: Whether to re-raise the exception after logging
        fallback: Value to return if an exception occurs and reraise=False
        context: Additional context to include in error logs
    
    Returns:
        Decorated function
    
    Example:
        @handle_errors(reraise=False, fallback=[])
        def safe_list_processing(data):
            return [process(item) for item in data]
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = get_logger(func.__module__)
            func_context = {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            }
            if context:
                func_context.update(context)
            
            try:
                return func(*args, **kwargs)
            except DiscrepancyError as e:
                level = log_level or EXCEPTION_LOG_LEVELS.get(type(e), logging.ERROR)
                log_with_context(
                    logger, 
                    logging.getLevelName(level), 
                    f"Discrepancy error in {func.__name__}: {str(e)}",
                    **func_context,
                    error_code=e.code,
                    exception_type=type(e).__name__
                )
                if reraise:
                    raise
                return fallback
            except Exception as e:
                level = log_level or EXCEPTION_LOG_LEVELS.get(Exception, logging.ERROR)
                error_traceback = traceback.format_exc()
                log_with_context(
                    logger,
                    logging.getLevelName(level),
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    **func_context,
                    exception_type=type(e).__name__,
                    traceback=error_traceback
                )
                if reraise:
                    raise
                return fallback
        
        return wrapper
    return decorator

def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    error_class: type = MissingDataError,
    error_message_template: str = "Missing required field(s): {missing_fields}"
) -> None:
    """
    Validate that all required fields are present in a data dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        error_class: Exception class to raise if validation fails
        error_message_template: Template for error message (supports {missing_fields})
    
    Raises:
        error_class: If any required fields are missing
    
    Example:
        validate_required_fields(
            data, 
            ['precinct_sum', 'county_reported'],
            error_class=MissingDataError
        )
    """
    missing = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing:
        message = error_message_template.format(missing_fields=", ".join(missing))
        raise error_class(
            message,
            missing_fields=missing,
            context={"data_keys": list(data.keys()), "required": required_fields}
        )

def safe_execute(
    func: Callable[..., T],
    *args,
    fallback: Optional[Any] = None,
    log_errors: bool = True,
    **kwargs
) -> T:
    """
    Execute a function with safe error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        fallback: Value to return if an exception occurs
        log_errors: Whether to log the error
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result or fallback value
    """
    logger = get_logger(func.__module__)
    
    try:
        return func(*args, **kwargs)
    except DiscrepancyError as e:
        if log_errors:
            log_with_context(
                logger,
                "ERROR",
                f"Discrepancy error in {func.__name__}: {str(e)}",
                function=func.__name__,
                error_code=e.code
            )
        return fallback
    except Exception as e:
        if log_errors:
            log_with_context(
                logger,
                "ERROR",
                f"Error in {func.__name__}: {str(e)}",
                function=func.__name__,
                exception_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
        return fallback

def error_handler_factory(
    default_error_class: type = DiscrepancyError,
    default_code: str = "GENERIC_001"
) -> Callable:
    """
    Factory function to create custom error handlers for specific contexts.
    
    Args:
        default_error_class: Default exception class to use
        default_code: Default error code
    
    Returns:
        Error handling decorator
    """
    def custom_handler(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = get_logger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                log_with_context(
                    logger,
                    "ERROR",
                    f"Error in {func.__name__}: {str(e)}",
                    function=func.__name__,
                    exception_type=type(e).__name__
                )
                
                # Wrap in our custom exception if not already one
                if not isinstance(e, DiscrepancyError):
                    raise default_error_class(
                        f"Operation failed in {func.__name__}: {str(e)}",
                        code=default_code,
                        context={"original_exception": str(e)}
                    )
                raise
        return wrapper
    return custom_handler

def log_function_call(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log function entry and exit with arguments.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    """
    logger = get_logger(func.__module__)
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        # Log entry
        log_with_context(
            logger,
            "DEBUG",
            f"Entering {func.__name__}",
            function=func.__name__,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )
        
        try:
            result = func(*args, **kwargs)
            log_with_context(
                logger,
                "DEBUG",
                f"Exiting {func.__name__} successfully",
                function=func.__name__
            )
            return result
        except Exception as e:
            log_with_context(
                logger,
                "ERROR",
                f"Exiting {func.__name__} with error: {str(e)}",
                function=func.__name__,
                exception_type=type(e).__name__
            )
            raise
    
    return wrapper

def validate_input_types(
    expected_types: Dict[str, type],
    error_class: type = ConfigurationError
) -> Callable:
    """
    Decorator factory to validate input parameter types.
    
    Args:
        expected_types: Dictionary mapping parameter names to expected types
        error_class: Exception class to raise on type mismatch
    
    Returns:
        Decorator for type validation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create a mapping of parameter names to values
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate types
            for param_name, expected_type in expected_types.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise error_class(
                            f"Parameter '{param_name}' expected {expected_type.__name__}, "
                            f"got {type(value).__name__}",
                            config_key=param_name,
                            expected_type=expected_type.__name__
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
