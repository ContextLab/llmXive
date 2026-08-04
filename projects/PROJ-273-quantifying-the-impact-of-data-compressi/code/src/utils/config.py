"""
Configuration management for the llmXive compression impact pipeline.

Provides:
- Random seed pinning for reproducibility
- Path management for project directories
- Global configuration constants
"""

import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import json

# Project root is assumed to be the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_ROOT = Path(__file__).resolve().parent.parent

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_TIMEOUT = 300  # seconds
MAX_INJECTION_ATTEMPTS = 20
MIN_VALID_EVENTS = 12
TARGET_VALID_EVENTS = 15

# Compression parameters
COMPRESSION_LEVELS = [1, 5, 9]
QUANTIZATION_BIT_WIDTHS = [8, 4]
JPEG2000_TARGET_DIMS = (2048, 1024)

# PE parameters (Fast PE per Amended FR-005)
PE_MAXITER = 5000
PE_NLIVE = 200
PE_DLOGZ_INIT = 0.5

# Statistical test parameters
STAT_ALPHA = 0.05
MIN_ESS = 100  # Minimum effective sample size for hierarchical test

# Paths relative to project root
PATHS = {
    'data_raw': 'data/raw',
    'data_interim': 'data/interim',
    'data_processed': 'data/processed',
    'data_external': 'data/external',
    'data_interim_compressed': 'data/interim/compressed',
    'figures': 'figures',
    'reports': 'reports',
    'specs': 'specs/001-compression-impact-gw-reconstruction',
    'provenance': 'code/provenance',
}

# Compression output subdirectories
COMPRESSION_OUTPUTS = {
    'lossless': 'data/interim/compressed/lossless',
    'quantization': 'data/interim/compressed/quantization',
    'wavelet': 'data/interim/compressed/wavelet',
    'jpeg2000': 'data/interim/compressed/jpeg2000',
}

# Baseline and report paths
BASELINE_PATH = 'data/external/baseline_bias_original.json'
FINAL_SUMMARY_PATH = 'reports/final_summary.md'


def get_project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT


def get_src_root() -> Path:
    """Return the src root directory."""
    return _SRC_ROOT


def get_path(key: str) -> Path:
    """
    Get an absolute path for a configured path key.

    Args:
        key: One of the keys in PATHS or COMPRESSION_OUTPUTS

    Returns:
        Absolute Path object
    """
    if key in PATHS:
        relative = PATHS[key]
    elif key in COMPRESSION_OUTPUTS:
        relative = COMPRESSION_OUTPUTS[key]
    else:
        raise ValueError(f"Unknown path key: {key}")

    return _PROJECT_ROOT / relative


def ensure_dir(path: Optional[Path] = None, key: Optional[str] = None) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Direct Path object (mutually exclusive with key)
        key: Path configuration key (mutually exclusive with path)

    Returns:
        The ensured Path object
    """
    if path is None and key is None:
        raise ValueError("Either 'path' or 'key' must be provided")
    if path is not None and key is not None:
        raise ValueError("Only one of 'path' or 'key' can be provided")

    target = path if path else get_path(key)
    target.mkdir(parents=True, exist_ok=True)
    return target


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility.

    Args:
        seed: Random seed value. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set
    """
    if seed is None:
        seed = DEFAULT_SEED

    random.seed(seed)
    # Note: numpy seed is set in modules that use numpy
    # torch seed is set in modules that use torch
    # This function handles the standard library random module

    return seed


def get_config() -> Dict[str, Any]:
    """
    Get a dictionary of all configuration values.

    Returns:
        Dictionary of configuration key-value pairs
    """
    return {
        'seed': DEFAULT_SEED,
        'timeout': DEFAULT_TIMEOUT,
        'max_injection_attempts': MAX_INJECTION_ATTEMPTS,
        'min_valid_events': MIN_VALID_EVENTS,
        'target_valid_events': TARGET_VALID_EVENTS,
        'compression_levels': COMPRESSION_LEVELS,
        'quantization_bit_widths': QUANTIZATION_BIT_WIDTHS,
        'jpeg2000_target_dims': JPEG2000_TARGET_DIMS,
        'pe_maxiter': PE_MAXITER,
        'pe_nlive': PE_NLIVE,
        'pe_dlogz_init': PE_DLOGZ_INIT,
        'stat_alpha': STAT_ALPHA,
        'min_ess': MIN_ESS,
        'paths': {k: str(v) for k, v in PATHS.items()},
        'compression_outputs': {k: str(v) for k, v in COMPRESSION_OUTPUTS.items()},
        'baseline_path': BASELINE_PATH,
        'final_summary_path': FINAL_SUMMARY_PATH,
    }


def save_config(output_path: Optional[Path] = None) -> Path:
    """
    Save current configuration to a JSON file.

    Args:
        output_path: Optional path to save config. If None, saves to
                    data/processed/config.json

    Returns:
        Path to the saved config file
    """
    if output_path is None:
        output_path = get_path('data_processed') / 'config.json'
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = get_config()
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

    return output_path


def hash_config() -> str:
    """
    Generate a hash of the current configuration for reproducibility tracking.

    Returns:
        SHA256 hash string of the configuration
    """
    config_str = json.dumps(get_config(), sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


# Initialize default seed on module import
_current_seed = set_seed()

__all__ = [
    'get_project_root',
    'get_src_root',
    'get_path',
    'ensure_dir',
    'set_seed',
    'get_config',
    'save_config',
    'hash_config',
    'DEFAULT_SEED',
    'DEFAULT_TIMEOUT',
    'MAX_INJECTION_ATTEMPTS',
    'MIN_VALID_EVENTS',
    'TARGET_VALID_EVENTS',
    'COMPRESSION_LEVELS',
    'QUANTIZATION_BIT_WIDTHS',
    'JPEG2000_TARGET_DIMS',
    'PE_MAXITER',
    'PE_NLIVE',
    'PE_DLOGZ_INIT',
    'STAT_ALPHA',
    'MIN_ESS',
    'PATHS',
    'COMPRESSION_OUTPUTS',
    'BASELINE_PATH',
    'FINAL_SUMMARY_PATH',
    '_current_seed',
]
