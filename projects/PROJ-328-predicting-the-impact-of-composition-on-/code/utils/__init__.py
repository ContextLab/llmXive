"""
Utility module for the Solder Hardness Prediction Pipeline.

This package provides common utilities for error handling, logging,
and other cross-cutting concerns.
"""
from .error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    DataInsufficientError,
    CompositionSumError
)
from .logging_config import setup_logging, get_logger

__all__ = [
    "SolderPipelineError",
    "ConfigurationError",
    "DataValidationError",
    "IngestionError",
    "ModelTrainingError",
    "DataInsufficientError",
    "CompositionSumError",
    "setup_logging",
    "get_logger"
]
