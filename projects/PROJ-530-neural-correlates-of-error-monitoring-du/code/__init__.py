"""
llmXive Research Pipeline - Code Package

This package provides the core implementation for the neural correlates
of error monitoring analysis pipeline.
"""

from .config_loader import load_config, validate_config, get_config_value, save_config, create_default_config
from .utils import set_global_seed, get_seed_status
from .logging_config import get_logger, initialize_logging, log_step, log_preprocessing_parameter, log_artifact
from .preprocess import calculate_angular_deviation, apply_filters, run_ica, save_preprocessing_log, extract_mfn_features, process_eeg_data, main as preprocess_main
from .analysis import FeasibilityError, load_processed_data, fit_linear_mixed_effects_model, run_sensitivity_sweep, main as analysis_main
from .viz import load_processed_data_for_viz, generate_scatter_plot_with_regression, generate_multi_electrode_comparison, main as viz_main
from .setup_directories import create_project_directories
from .linting_config import get_flake8_command, get_black_command, run_linter, run_formatter, create_config_files
