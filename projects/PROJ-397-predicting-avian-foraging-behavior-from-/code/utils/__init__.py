"""
Utility modules for the llmXive automated science pipeline.

This package provides shared functionality for:
- Configuration management (paths, seeds, constants)
- Data provenance tracking (hashing, metadata logging)
- Resource validation (runtime, memory constraints)
"""

from .config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_dir,
    get_models_dir,
    get_viz_dir,
    get_figures_dir,
    get_reports_dir,
    ensure_directories,
    get_seed,
    set_seed,
    get_model_params,
    get_cv_params,
    get_permutation_params,
    get_data_thresholds,
    get_file_paths,
    get_file_path
)

from .provenance import (
    compute_file_hash,
    compute_data_hash,
    generate_provenance_record,
    save_provenance_record,
    log_step,
    verify_data_integrity,
    load_provenance_records
)

__all__ = [
    # Config exports
    'get_project_root',
    'get_data_dir',
    'get_raw_data_dir',
    'get_processed_dir',
    'get_models_dir',
    'get_viz_dir',
    'get_figures_dir',
    'get_reports_dir',
    'ensure_directories',
    'get_seed',
    'set_seed',
    'get_model_params',
    'get_cv_params',
    'get_permutation_params',
    'get_data_thresholds',
    'get_file_paths',
    'get_file_path',
    # Provenance exports
    'compute_file_hash',
    'compute_data_hash',
    'generate_provenance_record',
    'save_provenance_record',
    'log_step',
    'verify_data_integrity',
    'load_provenance_records'
]