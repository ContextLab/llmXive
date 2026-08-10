"""
Utility modules for the llmXive automated science pipeline.

This package contains utility functions and classes used across
the project for common operations like configuration, validation,
hashing, and imputation.
"""
from .config import ConfigError, ProjectConfig, get_config, reset_config, EnvConfig, EnvConfigError
from .hashing import compute_file_hash, compute_string_hash, verify_file_hash, generate_manifest, load_manifest
from .imputation import impute_missing_values
from .validation import check_replicates, validate_data_types, validate_environmental_metadata, generate_validation_report

__all__ = [
    # Config
    'ConfigError',
    'ProjectConfig', 
    'get_config',
    'reset_config',
    'EnvConfig',
    'EnvConfigError',
    # Hashing
    'compute_file_hash',
    'compute_string_hash',
    'verify_file_hash',
    'generate_manifest',
    'load_manifest',
    # Imputation
    'impute_missing_values',
    # Validation
    'check_replicates',
    'validate_data_types',
    'validate_environmental_metadata',
    'generate_validation_report'
]
