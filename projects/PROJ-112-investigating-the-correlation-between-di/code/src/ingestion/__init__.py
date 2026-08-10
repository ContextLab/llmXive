"""
Ingestion module for downloading and preparing data.
"""
from .agp_loader import fetch_agp_data
from .ukbb_loader import fetch_ukbb_data
from .harmonizer import harmonize_and_merge
from .validation import validate_and_record
from .logging_config import (
    log_download_status,
    log_filter_counts,
    log_harmonization_result,
    log_merge_result,
    log_validation_result
)

__all__ = [
    'fetch_agp_data',
    'fetch_ukbb_data',
    'harmonize_and_merge',
    'validate_and_record',
    'log_download_status',
    'log_filter_counts',
    'log_harmonization_result',
    'log_merge_result',
    'log_validation_result'
]