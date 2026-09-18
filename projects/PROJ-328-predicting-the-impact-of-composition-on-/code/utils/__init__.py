"""
Utilities module for the Solder Hardness Prediction Pipeline.

This package provides shared utility functions including:
- Logging configuration and formatters
- Custom exception handlers
- Warning injection for FR-007 compliance
- Reference validation helpers
"""

from utils.logger import JSONFormatter, get_logger, init_project_logger, create_module_logger, log, log_with_extra
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
from utils.reference_validator import (
    validate_url,
    validate_citation_format,
    validate_research_md,
    ConstitutionError
)

__all__ = [
    # Logging
    'JSONFormatter',
    'get_logger',
    'init_project_logger',
    'create_module_logger',
    'log',
    'log_with_extra',
    
    # Error Handling
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
    'add_warning_to_text_file',
    
    # Reference Validation
    'validate_url',
    'validate_citation_format',
    'validate_research_md',
    'ConstitutionError'
]