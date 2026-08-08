import logging
import traceback
from functools import wraps
from typing import Callable, Optional, Any, Type
from code.utils.logger import get_pipeline_logger

class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Raised when data retrieval fails."""
    pass

class DataProcessingError(PipelineError):
    """Raised when data processing (descriptors, cleaning) fails."""
    pass

class ModelTrainingError(PipelineError):
    """Raised when model training or evaluation fails."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration validation fails."""
    pass

def handle_error(
    exception: Exception,
    context: str = "Unknown",
    log_level: int = logging.ERROR
) -> None:
    """
    Centralized error handling function.
    
    Args:
        exception: The exception instance to handle.
        context: A string describing the context where the error occurred.
        log_level: The logging level to use for the error message.
    
    Raises:
        The original exception after logging, allowing the caller to catch it.
    """
    logger = get_pipeline_logger()
    
    error_msg = f"Error in {context}: {str(exception)}"
    exc_traceback = traceback.format_exc()
    
    logger.log(log_level, error_msg)
    logger.log(log_level, f"Traceback:\n{exc_traceback}")
    
    # Re-raise to allow upstream handling or termination
    raise exception

def validate_not_null(value: Any, field_name: str) -> None:
    """
    Validates that a value is not None.
    
    Args:
        value: The value to check.
        field_name: The name of the field for error messaging.
    
    Raises:
        DataProcessingError: If the value is None.
    """
    if value is None:
        raise DataProcessingError(f"Validation failed: '{field_name}' cannot be null.")

def validate_positive(value: float, field_name: str) -> None:
    """
    Validates that a numeric value is strictly positive.
    
    Args:
        value: The value to check.
        field_name: The name of the field for error messaging.
    
    Raises:
        DataProcessingError: If the value is not positive.
    """
    if value is None or value <= 0:
        raise DataProcessingError(f"Validation failed: '{field_name}' must be a positive number.")

def pipeline_error_handler(func: Callable) -> Callable:
    """
    Decorator to wrap a function with centralized error handling.
    
    Args:
        func: The function to wrap.
    
    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e, context=f"Function {func.__name__}")
    return wrapper
