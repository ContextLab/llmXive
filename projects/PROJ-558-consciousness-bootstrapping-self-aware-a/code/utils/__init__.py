"""
Utils package for the Consciousness Bootstrapping project.
Contains logging, memory profiling, linting checks, and validation utilities.
"""
from .logging import (
    ConsciousnessBootstrappingError, ConfigurationError, DataLoadError,
    ModelTrainingError, EvaluationError, RecursionDepthError,
    setup_logging, get_logger, log_exception, log_training_start,
    log_training_end, log_evaluation_start, log_metric
)
from .memory_profiler import (
    get_current_memory_mb, get_peak_memory_mb, profile_training_script,
    get_peak_mb, main
)
from .lint_check import run_command, check_ruff, check_black, main