"""
Data module for the Social Support Resilience pipeline.

This module contains all data ingestion, preprocessing, and cohort construction code.
"""

from .ingestion import load_config, calculate_md5, download_dataset, load_cyber_data, load_gss_data, harmonize_datasets, get_data_summary, validate_schema_presence, run_ingestion_checks, main as ingestion_main
from .preprocessing import load_config, handle_high_missingness, check_convergence, apply_mice_imputation, apply_scale_scoring, apply_binary_exposure, handle_outcome_missingness, run_preprocessing, main as preprocessing_main
from .cohort import load_preprocessed_data, filter_critical_missing, check_harassment_variance, construct_analysis_cohort, save_cohort, validate_analysis_cohort, main as cohort_main
from .verify_columns import load_config, verify_platform_column, main as verify_columns_main
from .verify_data_dict import find_data_dictionary_table, parse_table_rows, verify_alignment, main as verify_data_dict_main
from .verify_methodology import find_section_5, verify_alignment, main as verify_methodology_main
from .verify_spec_alignment import verify_spec_alignment, main as verify_spec_alignment_main
from .verify_spec_state import verify_spec_state as verify_spec_state_func

__all__ = [
    'load_config', 'calculate_md5', 'download_dataset', 'load_cyber_data', 'load_gss_data', 'harmonize_datasets', 'get_data_summary', 'validate_schema_presence', 'run_ingestion_checks', 'ingestion_main',
    'handle_high_missingness', 'check_convergence', 'apply_mice_imputation', 'apply_scale_scoring', 'apply_binary_exposure', 'handle_outcome_missingness', 'run_preprocessing', 'preprocessing_main',
    'load_preprocessed_data', 'filter_critical_missing', 'check_harassment_variance', 'construct_analysis_cohort', 'save_cohort', 'validate_analysis_cohort', 'cohort_main',
    'verify_platform_column', 'verify_columns_main',
    'find_data_dictionary_table', 'parse_table_rows', 'verify_alignment', 'verify_data_dict_main',
    'find_section_5', 'verify_methodology_main',
    'verify_spec_alignment', 'verify_spec_alignment_main',
    'verify_spec_state_func'
]
