"""
Code package initialization.
Exports main classes and functions for the project.
"""
from .download import compute_md5, fetch_with_retry, save_dataset, download_all
from .featurize import (
    get_memory_usage_gb, load_raw_data, featurize_composition,
    featurize_dataframe, stratified_split, process_dataset, main
)
from .config import Config, get_config, reload_config
from .utils.logger import (
    setup_logger, get_logger, log_convergence_failure,
    log_memory_overflow, log_pipeline_start, log_pipeline_end
)
from .utils.schema_utils import (
    validate_per_sample_errors, save_schema_contract, create_empty_schema_example
)
from .stats.significance import run_paired_wilcoxon, run_sensitivity_analysis
from .models.gpr import run_gpr
from .models.mc_dropout import run_mc_dropout
from .models.deep_ensemble import run_deep_ensemble
from .models.conformal import run_conformal_prediction

__all__ = [
    # Download
    'compute_md5', 'fetch_with_retry', 'save_dataset', 'download_all',
    # Featurize
    'get_memory_usage_gb', 'load_raw_data', 'featurize_composition',
    'featurize_dataframe', 'stratified_split', 'process_dataset', 'main',
    # Config
    'Config', 'get_config', 'reload_config',
    # Logger
    'setup_logger', 'get_logger', 'log_convergence_failure',
    'log_memory_overflow', 'log_pipeline_start', 'log_pipeline_end',
    # Schema
    'validate_per_sample_errors', 'save_schema_contract', 'create_empty_schema_example',
    # Stats
    'run_paired_wilcoxon', 'run_sensitivity_analysis',
    # Models
    'run_gpr', 'run_mc_dropout', 'run_deep_ensemble', 'run_conformal_prediction'
]