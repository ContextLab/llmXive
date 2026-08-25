"""
Configuration management package for the CTCF binding site selection project.
Handles environment variables, API keys, and local path resolution.
"""
from .config_loader import (
    load_env_config,
    validate_manifest_exists,
    get_encode_api_key,
    get_data_paths,
    ensure_directories,
    write_sample_config,
    get_config_value,
    ConfigError
)

__all__ = [
    'load_env_config',
    'validate_manifest_exists',
    'get_encode_api_key',
    'get_data_paths',
    'ensure_directories',
    'write_sample_config',
    'get_config_value',
    'ConfigError'
]
