"""Custom error handlers for the pipeline."""
from typing import Optional, Dict, Any
import logging
from utils.logging_config import get_logger

class SolderPipelineError(Exception):
    """Base exception for the solder pipeline."""
    pass

class ConfigurationError(SolderPipelineError):
    """Raised when a configuration is invalid or missing."""
    pass

class DataValidationError(SolderPipelineError):
    """Raised when data validation fails."""
    pass

class IngestionError(SolderPipelineError):
    """Raised when data ingestion fails."""
    pass

class ModelTrainingError(SolderPipelineError):
    """Raised when model training fails."""
    pass

class DataInsufficientError(SolderPipelineError):
    """Raised when data is insufficient for the task."""
    pass

class CompositionSumError(SolderPipelineError):
    """Raised when composition sum is invalid."""
    pass

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log an error with optional context."""
    logger = get_logger(__name__)
    logger.error(f"Error: {str(error)}", exc_info=True, extra=context)
