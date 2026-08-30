"""
Utility functions and infrastructure.

Exports:
  - Config, get_config, set_config, validate_config
  - ConsciousnessBootstrappingError, ConfigurationError, DataLoadError
  - ModelTrainingError, EvaluationError, RecursionDepthError
  - setup_logging, get_logger, log_exception
  - log_training_start, log_training_end, log_evaluation_start, log_metric
  - get_current_memory_mb, get_peak_memory_mb, get_peak_mb
  - profile_training_script
  - run_command, check_ruff, check_black
"""
from .config import Config, get_config, set_config, validate_config
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
    get_peak_mb,
    profile_training_script
)
from .lint_check import run_command, check_ruff, check_black