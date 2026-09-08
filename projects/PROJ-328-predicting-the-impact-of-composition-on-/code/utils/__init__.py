"""
Utility modules for the Solder Hardness Prediction Pipeline.

This package provides shared utilities including logging, error handling,
reference validation, and compositional data warnings.
"""

from utils.logger import JSONFormatter, get_logger, init_project_logger, create_module_logger, log
from utils.logging_config import setup_logging, get_logger as get_config_logger, init_project_logger as init_config_logger
from utils.error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    DataInsufficientError,
    CompositionSumError,
    log_error
)
from utils.fr007_warnings import (
    get_warning_header,
    inject_warning_into_json_output,
    inject_warning_into_yaml_output,
    add_warning_to_text_file
)

__all__ = [
    # Logger
    'JSONFormatter',
    'get_logger',
    'init_project_logger',
    'create_module_logger',
    'log',
    'setup_logging',
    'get_config_logger',
    'init_config_logger',
    # Error Handlers
    'SolderPipelineError',
    'ConfigurationError',
    'DataValidationError',
    'IngestionError',
    'ModelTrainingError',
    'DataInsufficientError',
    'CompositionSumError',
    'log_error',
    # Warnings
    'get_warning_header',
    'inject_warning_into_json_output',
    'inject_warning_into_yaml_output',
    'add_warning_to_text_file'
]