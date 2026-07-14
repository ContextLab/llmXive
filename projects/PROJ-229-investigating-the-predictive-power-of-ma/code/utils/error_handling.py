import logging
import traceback
from functools import wraps
from typing import Callable, Optional, Any
from code.utils.logger import get_pipeline_logger

class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataFetchError(PipelineError):
    """Error occurred while fetching data from external sources."""
    pass

class DataProcessingError(PipelineError):
    """Error occurred during data processing or transformation."""
    pass

class ModelTrainingError(PipelineError):
    """Error occurred during model training or evaluation."""
    pass

class ConfigError(PipelineError):
    """Error related to configuration loading or validation."""
    pass

def handle_error(
    error: Exception,
    context: str = "",
    raise_on_error: bool = True,
    log_level: int = logging.ERROR
) -> Optional[Exception]:
    """
    Centralized error handling utility.
    
    Args:
        error: The exception instance to handle
        context: Additional context about where the error occurred
        raise_on_error: If True, re-raise the exception after logging
        log_level: Logging level for the error message
        
    Returns:
        The exception instance if raise_on_error is False, None otherwise
    """
    logger = get_pipeline_logger()
    full_context = f"{context}: " if context else ""
    error_trace = traceback.format_exc()
    
    error_msg = f"{full_context}{type(error).__name__}: {str(error)}"
    logger.log(log_level, error_msg)
    logger.debug(f"Traceback:\n{error_trace}")
    
    if raise_on_error:
        raise error
    return error

def validate_not_null(
    value: Any,
    field_name: str,
    context: str = ""
) -> None:
    """
    Validate that a value is not None.
    
    Args:
        value: The value to check
        field_name: Name of the field for error reporting
        context: Optional context for the error
        
    Raises:
        DataProcessingError: If value is None
    """
    if value is None:
        error_msg = f"Validation failed: {field_name} cannot be None"
        if context:
            error_msg = f"{context}: {error_msg}"
        raise DataProcessingError(error_msg, {"field": field_name})

def validate_positive(
    value: float,
    field_name: str,
    context: str = ""
) -> None:
    """
    Validate that a numeric value is positive.
    
    Args:
        value: The value to check
        field_name: Name of the field for error reporting
        context: Optional context for the error
        
    Raises:
        DataProcessingError: If value is not positive
    """
    if not isinstance(value, (int, float)):
        error_msg = f"Validation failed: {field_name} must be numeric"
        if context:
            error_msg = f"{context}: {error_msg}"
        raise DataProcessingError(error_msg, {"field": field_name, "value": value})
    
    if value <= 0:
        error_msg = f"Validation failed: {field_name} must be positive"
        if context:
            error_msg = f"{context}: {error_msg}"
        raise DataProcessingError(error_msg, {"field": field_name, "value": value})

def pipeline_error_handler(
    func: Callable
) -> Callable:
    """
    Decorator to automatically handle errors in pipeline functions.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(
                e,
                context=f"Error in function '{func.__name__}'",
                raise_on_error=True
            )
    return wrapper