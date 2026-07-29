"""
Utilities package for the Consciousness Bootstrapping project.
Contains logging, error handling, memory profiling, and linting utilities.
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
    log_metric
)
from .memory_profiler import (
    get_current_memory_mb,
    get_peak_memory_mb,
    profile_training_script,
    get_peak_mb,
    main
)
from .lint_check import run_command, check_ruff, check_black, main as lint_main

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
    "get_current_memory_mb",
    "get_peak_memory_mb",
    "profile_training_script",
    "get_peak_mb",
    "run_command",
    "check_ruff",
    "check_black"
]