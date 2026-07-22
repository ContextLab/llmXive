"""
Utilities package for Consciousness Bootstrapping.
Exports: Logging exceptions, setup_logging, get_logger, and helper log functions.
"""
from .logging import (
    ConsciousnessBootstrappingError,
    ConfigurationError,
    DataLoadError,
    ModelTrainingError,
    EvaluationError,
    RecursionDepthError,
    setup_logging,
    get_logger,
    log_exception,
    log_training_start,
    log_training_end,
    log_evaluation_start,
    log_metric,
)

__all__ = [
    "ConsciousnessBootstrappingError",
    "ConfigurationError",
    "DataLoadError",
    "ModelTrainingError",
    "EvaluationError",
    "RecursionDepthError",
    "setup_logging",
    "get_logger",
    "log_exception",
    "log_training_start",
    "log_training_end",
    "log_evaluation_start",
    "log_metric",
]