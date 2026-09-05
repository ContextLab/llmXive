import logging
import traceback
from functools import wraps
from typing import Callable, Optional, Any, Type

from code.utils.logger import get_pipeline_logger

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Raised when data fetching fails."""
    pass

class DataProcessingError(PipelineError):
    """Raised when data processing fails."""
    pass

class ModelTrainingError(PipelineError):
    """Raised when model training fails."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration is invalid."""
    pass

def handle_error(
    error: Exception,
    context: str = "Pipeline Error",
    log_level: int = logging.ERROR,
    reraise: bool = True
) -> None:
    """
    Handle an error by logging it and optionally raising it.
    
    Args:
        error: The exception to handle.
        context: A string describing the context where the error occurred.
        log_level: The logging level to use (e.g., logging.ERROR, logging.WARNING).
        reraise: Whether to re-raise the exception after logging.
    
    Raises:
        The original exception if reraise is True.
    """
    logger = get_pipeline_logger()
    logger.log(log_level, f"{context}: {error.__class__.__name__} - {str(error)}")
    logger.debug(f"Traceback: {''.join(traceback.format_exception(type(error), error, error.__traceback__))}")
    
    if reraise:
        raise error

def validate_not_null(value: Any, field_name: str) -> None:
    """
    Validate that a value is not None.
    
    Args:
        value: The value to validate.
        field_name: The name of the field for error messaging.
    
    Raises:
        ConfigError: If the value is None.
    """
    if value is None:
        error = ConfigError(f"{field_name} cannot be None")
        handle_error(error, "Validation Error")

def validate_positive(value: float, field_name: str) -> None:
    """
    Validate that a numeric value is positive.
    
    Args:
        value: The value to validate.
        field_name: The name of the field for error messaging.
    
    Raises:
        ConfigError: If the value is not positive.
    """
    if value is None or value <= 0:
        error = ConfigError(f"{field_name} must be a positive number")
        handle_error(error, "Validation Error")

def pipeline_error_handler(
    context: str = "Pipeline Error",
    reraise: bool = True
):
    """
    Decorator to handle errors in pipeline functions.
    
    Args:
        context: A string describing the context where the error occurred.
        reraise: Whether to re-raise the exception after logging.
    
    Returns:
        The wrapped function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context, reraise=reraise)
        return wrapper
    return decorator
