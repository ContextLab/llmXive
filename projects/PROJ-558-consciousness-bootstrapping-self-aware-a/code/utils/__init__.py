"""
Utility functions: logging, config, memory profiling, linting.
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
from .config import Config, get_config, set_config, validate_config, main as config_main
from .memory_profiler import (
    get_current_memory_mb,
    get_peak_memory_mb,
    get_peak_mb,
    profile_training_script,
    main as profile_main
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
    "Config",
    "get_config",
    "set_config",
    "validate_config",
    "config_main",
    "get_current_memory_mb",
    "get_peak_memory_mb",
    "get_peak_mb",
    "profile_training_script",
    "profile_main",
    "run_command",
    "check_ruff",
    "check_black",
    "lint_main"
]