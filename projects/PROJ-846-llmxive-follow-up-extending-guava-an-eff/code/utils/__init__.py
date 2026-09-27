"""
Utils package initialization.

Exports custom exception classes and utility functions for the llmXive pipeline.
"""

from .errors import (
    LlmXiveError,
    DatasetUnavailableError,
    ConvergenceTimeoutError,
    PerceptionInferenceError,
    SymbolicTransformationError,
    ValidationThresholdError,
    BaselineUnavailableError,
    GroundTruthSchemaMissingError,
    EnvironmentConfigError,
)
from .config import (
    initialize_paths,
    get_path,
    set_hyperparameter,
    get_hyperparameter,
    set_global_seed,
    ensure_directories,
    get_config_summary,
)
from .state_manager import (
    get_project_root,
    calculate_file_hash,
    get_all_files,
    generate_state_hash,
    update_state_file,
    verify_state_integrity,
    get_state_summary,
    main as state_manager_main,
)
from .logger import (
    log_perception_ground_truth,
    log_latency,
    get_current_log_stats,
    clear_log,
)
from .environment_config import (
    EnvironmentConfigError as EnvConfigError,
    detect_cpu_count,
    verify_cpu_only_constraint,
    configure_torch_for_cpu,
    enforce_cpu_only,
    get_environment_summary,
    main as env_config_main,
)
from .complexity_report import (
    analyze_file,
    generate_report,
    main as complexity_report_main,
)

__all__ = [
    # Errors
    "LlmXiveError",
    "DatasetUnavailableError",
    "ConvergenceTimeoutError",
    "PerceptionInferenceError",
    "SymbolicTransformationError",
    "ValidationThresholdError",
    "BaselineUnavailableError",
    "GroundTruthSchemaMissingError",
    "EnvironmentConfigError",
    "EnvConfigError",
    # Config
    "initialize_paths",
    "get_path",
    "set_hyperparameter",
    "get_hyperparameter",
    "set_global_seed",
    "ensure_directories",
    "get_config_summary",
    # State Manager
    "get_project_root",
    "calculate_file_hash",
    "get_all_files",
    "generate_state_hash",
    "update_state_file",
    "verify_state_integrity",
    "get_state_summary",
    "state_manager_main",
    # Logger
    "log_perception_ground_truth",
    "log_latency",
    "get_current_log_stats",
    "clear_log",
    # Environment Config
    "detect_cpu_count",
    "verify_cpu_only_constraint",
    "configure_torch_for_cpu",
    "enforce_cpu_only",
    "get_environment_summary",
    "env_config_main",
    # Complexity Report
    "analyze_file",
    "generate_report",
    "complexity_report_main",
]