"""
Utilities package for the Solder Hardness Prediction Pipeline.

This package contains shared utilities for error handling and logging.
"""
from .error_handlers import (
    SolderPipelineError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    ConfigurationError
)
from .logging_config import setup_logging, get_logger
from .fr007_warnings import (
    get_warning_header,
    inject_warning_into_json_output,
    inject_warning_into_yaml_output,
    add_warning_to_text_file
)

__all__ = [
    'SolderPipelineError',
    'DataValidationError',
    'IngestionError',
    'ModelTrainingError',
    'ConfigurationError',
    'setup_logging',
    'get_logger',
    'get_warning_header',
    'inject_warning_into_json_output',
    'inject_warning_into_yaml_output',
    'add_warning_to_text_file'
]
