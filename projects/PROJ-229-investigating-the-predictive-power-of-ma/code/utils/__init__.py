"""
utils package initialization.

This module deliberately avoids eager imports of sub‑modules that depend on each
other (e.g., ``collinearity_utils``) to prevent circular‑import errors.
Only lightweight, dependency‑free utilities are imported here.
"""

# Re‑export the most commonly used logger utilities
from .logger import (
    setup_logger,
    get_pipeline_logger,
    log_debug,
    log_info,
    log_warning,
    log_error,
    log_critical,
    log_exception_details,
)

# Re‑export error‑handling classes and helpers
from .error_handling import (
    PipelineError,
    DataFetchError,
    DataProcessingError,
    ModelTrainingError,
    ConfigError,
    handle_error,
    validate_not_null,
    validate_positive,
    pipeline_error_handler,
)

__all__ = [
    "setup_logger",
    "get_pipeline_logger",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_critical",
    "log_exception_details",
    "PipelineError",
    "DataFetchError",
    "DataProcessingError",
    "ModelTrainingError",
    "ConfigError",
    "handle_error",
    "validate_not_null",
    "validate_positive",
    "pipeline_error_handler",
]
