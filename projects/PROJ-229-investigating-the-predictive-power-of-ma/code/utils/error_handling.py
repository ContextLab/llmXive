import logging
import traceback
from functools import wraps
from typing import Callable, Optional, Any, Type
from datetime import datetime

from code.utils.logger import get_pipeline_logger, log_error

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class DataFetchError(PipelineError):
    """Exception raised when data fetching fails."""
    pass

class DataProcessingError(PipelineError):
    """Exception raised when data processing fails."""
    pass

class ModelTrainingError(PipelineError):
    """Exception raised when model training fails."""
    pass

class ConfigError(PipelineError):
    """Exception raised when configuration is invalid."""
    pass

def handle_error(error: Exception, context: str = "Pipeline Error", reraise: bool = True) -> None:
    """
    Centralized error handling function.
    
    Args:
        error: The exception to handle.
        context: Contextual description of the error.
        reraise: If True, re-raises the exception after logging.
    """
    logger = get_pipeline_logger()
    log_error(error, context)
    
    if reraise:
        raise error

def validate_not_null(value: Any, field_name: str) -> Any:
    """
    Validate that a value is not None.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messaging.
    
    Returns:
        The value if valid.
    
    Raises:
        ValueError: If the value is None.
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")
    return value

def validate_positive(value: float, field_name: str) -> float:
    """
    Validate that a numeric value is positive.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messaging.
    
    Returns:
        The value if valid.
    
    Raises:
        ValueError: If the value is not positive.
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value

def pipeline_error_handler(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in pipeline functions.
    
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
            context = f"Error in {func.__name__}"
            handle_error(e, context)
            raise
    return wrapper
