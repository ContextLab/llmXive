import logging
import traceback
from functools import wraps
from typing import Callable, Optional, Any, Type
from code.utils.logger import get_pipeline_logger

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Raised when data retrieval fails."""
    pass

class DataProcessingError(PipelineError):
    """Raised when data processing/computation fails."""
    pass

class ModelTrainingError(PipelineError):
    """Raised when model training fails."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration is invalid or missing."""
    pass

def handle_error(
    error: Exception,
    context: str = "",
    raise_on_error: bool = True
) -> Optional[str]:
    """
    Centralized error handling logic.
    
    Args:
        error: The exception instance.
        context: Additional context about where the error occurred.
        raise_on_error: If True, re-raises the exception after logging.
    
    Returns:
        The error message if raise_on_error is False, else None.
    """
    logger = get_pipeline_logger()
    error_type = type(error).__name__
    error_msg = str(error)
    tb_str = traceback.format_exc()
    
    log_msg = f"Error in {context}: {error_type}: {error_msg}"
    logger.error(log_msg)
    logger.debug(tb_str)
    
    if raise_on_error:
        raise error
    
    return error_msg

def validate_not_null(value: Any, field_name: str) -> Any:
    """
    Validate that a value is not None.
    
    Args:
        value: The value to check.
        field_name: Name of the field for error context.
    
    Returns:
        The value if valid.
    
    Raises:
        ConfigError: If value is None.
    """
    if value is None:
        raise ConfigError(f"Field '{field_name}' cannot be None.")
    return value

def validate_positive(value: float, field_name: str) -> float:
    """
    Validate that a numeric value is positive.
    
    Args:
        value: The value to check.
        field_name: Name of the field for error context.
    
    Returns:
        The value if valid.
    
    Raises:
        DataProcessingError: If value is not positive.
    """
    if not isinstance(value, (int, float)):
        raise DataProcessingError(f"Field '{field_name}' must be numeric.")
    if value <= 0:
        raise DataProcessingError(f"Field '{field_name}' must be positive, got {value}.")
    return value

def pipeline_error_handler(
    context: str = ""
) -> Callable:
    """
    Decorator to wrap functions with standard error handling.
    
    Args:
        context: Context description for the error log.
    
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except PipelineError as e:
                handle_error(e, context or func.__name__, raise_on_error=True)
            except Exception as e:
                handle_error(e, context or func.__name__, raise_on_error=True)
        return wrapper
    return decorator