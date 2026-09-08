"""
Custom error handlers for the solder hardness prediction pipeline.
"""
from typing import Optional, Dict, Any
import logging

from utils.logging_config import get_logger

logger = get_logger("error_handlers")


class SolderPipelineError(Exception):
    """Base exception for the solder pipeline."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ConfigurationError(SolderPipelineError):
    """Raised when a configuration issue is detected."""
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
    """Raised when data is insufficient for analysis."""
    pass


class CompositionSumError(SolderPipelineError):
    """Raised when composition sum validation fails."""
    pass


def log_error(error: SolderPipelineError, context: Optional[str] = None) -> None:
    """
    Log an error with context.

    Args:
        error: The exception instance.
        context: Optional context about where the error occurred.
    """
    error_msg = f"{type(error).__name__}: {error}"
    if context:
        error_msg = f"[{context}] {error_msg}"

    logger.error(error_msg)
    if error.details:
        logger.error(f"Error details: {error.details}")
