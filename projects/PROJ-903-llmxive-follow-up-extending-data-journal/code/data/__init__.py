"""
Data package initialization.
Exports modules for loading, processing, and managing datasets.
"""
from .loader import (
    DataFetchError,
    RAMExceededError,
    LowPowerError,
    LowNumericColumnsError,
    compute_sha256,
    estimate_memory_usage,
    validate_numeric_columns,
    check_sample_size,
    fetch_dataset_from_hf,
    fetch_dataset_from_url,
    fetch_and_save_dataset,
    process_and_validate,
    load_all_datasets,
    main as loader_main
)

from .processor import (
    MissingValueError,
    detect_missing_values,
    handle_missing_values,
    generate_cleaning_report,
    generate_statistical_summaries,
    process_dataset,
    main as processor_main
)

from .registry import load_registry

from .dataset_registry import (
    compute_sha256 as ds_compute_sha256,
    fetch_and_save_dataset as ds_fetch_and_save,
    update_registry,
    verify_checksum
)

from .validate_registry import (
    validate_dataset_entry,
    validate_registry,
    main as validate_registry_main
)

__all__ = [
    'DataFetchError', 'RAMExceededError', 'LowPowerError', 'LowNumericColumnsError',
    'compute_sha256', 'estimate_memory_usage', 'validate_numeric_columns', 'check_sample_size',
    'fetch_dataset_from_hf', 'fetch_dataset_from_url', 'fetch_and_save_dataset',
    'process_and_validate', 'load_all_datasets', 'loader_main',
    'MissingValueError', 'detect_missing_values', 'handle_missing_values',
    'generate_cleaning_report', 'generate_statistical_summaries', 'process_dataset', 'processor_main',
    'load_registry',
    'ds_compute_sha256', 'ds_fetch_and_save', 'update_registry', 'verify_checksum',
    'validate_dataset_entry', 'validate_registry', 'validate_registry_main'
]