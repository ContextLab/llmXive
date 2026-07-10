"""
Data module initialization.

This module provides the base logging infrastructure for data operations
and re-exports core data loader and validation utilities.
"""
from code.data.data_loader import DataLoaderError, BaseDataLoader, validate_sampling_rate, validate_trial_counts
from code.data.download import validate_auditory_dataset, validate_visual_dataset, DownloadValidationError
from code.utils.logger import get_logger, configure_logging, LoggerError, LogConfigurationError

# Initialize module-level logger
logger = get_logger("code.data")

__all__ = [
    "DataLoaderError",
    "BaseDataLoader",
    "validate_sampling_rate",
    "validate_trial_counts",
    "validate_auditory_dataset",
    "validate_visual_dataset",
    "DownloadValidationError",
    "logger",
    "get_logger",
    "configure_logging",
    "LoggerError",
    "LogConfigurationError"
]