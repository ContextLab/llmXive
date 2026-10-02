"""
Data loading and preprocessing module.

This module provides utilities for loading, validating, and managing
neuroimaging and behavioral data sources.
"""

from code.data.paths import (
    get_project_root,
    get_raw_path,
    get_processed_path,
    get_results_path,
    ensure_dir
)
from code.data.loader import (
    load_nifti,
    load_behavioral_csv,
    validate_subject_data
)
from code.data.behavioral_validator import (
    load_behavioral_scores,
    identify_missing_scores,
    log_missing_score_exclusions,
    filter_missing_scores,
    run_behavioral_validation_pipeline
)

__all__ = [
    # Paths
    'get_project_root',
    'get_raw_path',
    'get_processed_path',
    'get_results_path',
    'ensure_dir',
    # Loader
    'load_nifti',
    'load_behavioral_csv',
    'validate_subject_data',
    # Behavioral Validation
    'load_behavioral_scores',
    'identify_missing_scores',
    'log_missing_score_exclusions',
    'filter_missing_scores',
    'run_behavioral_validation_pipeline'
]