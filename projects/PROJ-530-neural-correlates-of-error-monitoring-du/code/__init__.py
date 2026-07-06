"""
Neural Correlates of Error Monitoring During Simulated Navigation
Code package for PROJ-530.
"""
from .utils import set_global_seed, get_seed_status
from .logging_config import get_logger, initialize_logging, log_step, log_preprocessing_parameter, log_artifact
from .linting_config import get_flake8_command, get_black_command, run_linter, run_formatter, create_config_files
from .setup_directories import create_project_directories
from .preprocess import load_raw_data, apply_filters, run_ica, save_preprocessing_log, calculate_angular_deviation, extract_mfn_features, process_eeg_data, main
from .config_loader import (
    load_config,
    validate_config,
    get_config_value,
    save_config,
    create_default_config,
    DEFAULT_CONFIG
)

__version__ = "0.1.0"
__all__ = [
    "set_global_seed", "get_seed_status",
    "get_logger", "initialize_logging", "log_step", "log_preprocessing_parameter", "log_artifact",
    "get_flake8_command", "get_black_command", "run_linter", "run_formatter", "create_config_files",
    "create_project_directories",
    "load_raw_data", "apply_filters", "run_ica", "save_preprocessing_log",
    "calculate_angular_deviation", "extract_mfn_features", "process_eeg_data", "main",
    "load_config", "validate_config", "get_config_value", "save_config", 
    "create_default_config", "DEFAULT_CONFIG"
]