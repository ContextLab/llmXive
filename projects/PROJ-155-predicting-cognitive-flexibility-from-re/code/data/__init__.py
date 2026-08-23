"""
Data ingestion, preprocessing, and merging utilities.

This package provides utilities for:
- Downloading raw data (download.py)
- Loading NIfTI and behavioral data (loader.py)
- Preprocessing and parcellation (preprocess.py)
- Merging neuroimaging and behavioral data (merge.py)
- Validation and schema checking (validation.py, behavioral_validator.py)
- Path management (paths.py)
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
from code.data.download import (
    get_hcp_auth_token,
    calculate_sha256,
    fetch_manifest,
    verify_checksum,
    download_file,
    construct_hcp_url,
    download_subject_data,
    run_download_pipeline
)
from code.data.preprocess import (
    load_schaefer_parcellation,
    extract_roi_time_series,
    preprocess_subject,
    run_preprocessing_pipeline
)
from code.data.merge import (
    load_neuro_features,
    load_behavioral_scores,
    merge_datasets,
    validate_merged_schema,
    run_merge_pipeline
)
from code.data.validation import (
    validate_final_results_schema,
    validate_unique_subjects,
    validate_final_results_file,
    run_validation_pipeline
)
from code.data.behavioral_validator import (
    load_behavioral_scores as load_behavioral_scores_validator,
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
    
    # Download
    'get_hcp_auth_token',
    'calculate_sha256',
    'fetch_manifest',
    'verify_checksum',
    'download_file',
    'construct_hcp_url',
    'download_subject_data',
    'run_download_pipeline',
    
    # Preprocess
    'load_schaefer_parcellation',
    'extract_roi_time_series',
    'preprocess_subject',
    'run_preprocessing_pipeline',
    
    # Merge
    'load_neuro_features',
    'load_behavioral_scores',
    'merge_datasets',
    'validate_merged_schema',
    'run_merge_pipeline',
    
    # Validation
    'validate_final_results_schema',
    'validate_unique_subjects',
    'validate_final_results_file',
    'run_validation_pipeline',
    
    # Behavioral Validator
    'load_behavioral_scores_validator',
    'identify_missing_scores',
    'log_missing_score_exclusions',
    'filter_missing_scores',
    'run_behavioral_validation_pipeline'
]