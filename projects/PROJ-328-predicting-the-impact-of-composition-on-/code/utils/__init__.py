"""
Utility modules for the Solder Hardness Prediction Pipeline.

This package contains helper functions, error handlers, logging configurations,
and other shared utilities used across the ingestion, feature engineering,
modeling, and evaluation stages.
"""

# Import common utilities for convenience
from .logging_config import setup_logging, get_logger, init_project_logger
from .error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    DataInsufficientError,
    CompositionSumError,
    log_error
)
from .fr007_warnings import (
    get_warning_header,
    inject_warning_into_json_output,
    inject_warning_into_yaml_output,
    add_warning_to_text_file
)

__all__ = [
    # Logging
    'setup_logging',
    'get_logger',
    'init_project_logger',
    # Error Handlers
    'SolderPipelineError',
    'ConfigurationError',
    'DataValidationError',
    'IngestionError',
    'ModelTrainingError',
    'DataInsufficientError',
    'CompositionSumError',
    'log_error',
    # FR-007 Warnings
    'get_warning_header',
    'inject_warning_into_json_output',
    'inject_warning_into_yaml_output',
    'add_warning_to_text_file'
]