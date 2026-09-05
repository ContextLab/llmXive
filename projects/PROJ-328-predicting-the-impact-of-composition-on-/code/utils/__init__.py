"""
Utilities module for the Solder Hardness Prediction Pipeline.

This module provides shared utilities including logging, error handling,
reference validation, and compositional data warnings.
"""

from utils.logger import JSONFormatter, get_logger, init_project_logger, create_module_logger, log
from utils.logging_config import setup_logging, get_logger as get_logger_config
from utils.error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    DataInsufficientError,
    CompositionSumError,
    log_error,
)
from utils.fr007_warnings import (
    get_warning_header,
    inject_warning_into_json_output,
    inject_warning_into_yaml_output,
    add_warning_to_text_file,
)

__all__ = [
    "JSONFormatter",
    "get_logger",
    "init_project_logger",
    "create_module_logger",
    "log",
    "setup_logging",
    "get_logger_config",
    "SolderPipelineError",
    "ConfigurationError",
    "DataValidationError",
    "IngestionError",
    "ModelTrainingError",
    "DataInsufficientError",
    "CompositionSumError",
    "log_error",
    "get_warning_header",
    "inject_warning_into_json_output",
    "inject_warning_into_yaml_output",
    "add_warning_to_text_file",
]