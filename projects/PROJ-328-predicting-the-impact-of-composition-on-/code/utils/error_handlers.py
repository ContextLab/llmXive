"""
Custom exception classes and error handling utilities for the Solder Hardness Prediction Pipeline.
"""
from typing import Optional, Dict, Any
import logging
from utils.logging_config import get_logger

# Initialize module logger
_logger = get_logger("utils.error_handlers")

class SolderPipelineError(Exception):
    """Base exception for all pipeline errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        _logger.error(f"SolderPipelineError: {message}", extra={"context": self.context})

class ConfigurationError(SolderPipelineError):
    """Raised when a configuration issue is detected (e.g., missing files, invalid settings)."""
    pass

class DataValidationError(SolderPipelineError):
    """Raised when data validation fails (e.g., missing columns, invalid values)."""
    pass

class IngestionError(SolderPipelineError):
    """Raised when data ingestion (fetching/scraping) fails."""
    pass

class ModelTrainingError(SolderPipelineError):
    """Raised when model training or evaluation fails."""
    pass

class DataInsufficientError(SolderPipelineError):
    """Raised when the dataset is too small to proceed with analysis."""
    pass

class CompositionSumError(SolderPipelineError):
    """Raised when elemental composition sums do not meet the required threshold."""
    pass

def log_error(
    error: Exception,
    level: int = logging.ERROR,
    extra_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with standardized formatting and context.
    
    Args:
        error: The exception instance to log.
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        extra_context: Additional context dictionary to include in the log.
    """
    context = extra_context or {}
    context["exception_type"] = type(error).__name__
    context["exception_message"] = str(error)
    
    logger = get_logger("utils.error_handlers")
    logger.log(level, f"Error occurred: {error}", extra={"context": context})
    
    if hasattr(error, 'context') and error.context:
        logger.log(level, f"Error context: {error.context}", extra={"context": context})
