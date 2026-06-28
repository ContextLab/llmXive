"""
Configuration module for the code duplication research pipeline.

Centralizes all configurable parameters including random seeds, thresholds,
model parameters, and runtime limits for reproducibility (SC-005).
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration values
_DEFAULT_CONFIG = {
    # Random seed for reproducibility
    'random_seed': 42,

    # Clone detection thresholds (SC-007, T043)
    'clone_thresholds': [0.7, 0.8, 0.9],

    # Memory limits (SC-002, T023)
    'memory_limit_mb': 7000,

    # Runtime limits (SC-001)
    'max_runtime_seconds': 86400,  # 24 hours

    # Validation thresholds
    'min_valid_segments': 1000,  # SC-003

    # Statistical analysis
    'correlation_method': 'spearman',
    'significance_threshold': 0.05,

    # Visualization
    'figure_format': 'png',
    'figure_dpi': 300,

    # Checksum
    'checksum_algorithm': 'sha256',

    # Data sources
    'dataset_name': 'codeparrot/github-code',
    'model_name': 'Salesforce/codegen-350M-mono',
    'quantization_bits': 8,

    # Processing flags
    'streaming_enabled': True,
    'pii_scan_enabled': True,
}

# Runtime configuration (can be overridden)
_runtime_config: Dict[str, Any] = {}

def get_clone_thresholds() -> List[float]:
    """
    Get the list of clone detection thresholds for sensitivity analysis.

    Returns:
        List of threshold values (0.7, 0.8, 0.9) as per T043.
    """
    return _runtime_config.get('clone_thresholds', _DEFAULT_CONFIG['clone_thresholds'])

def get_random_seed() -> int:
    """
    Get the random seed for reproducibility.

    Returns:
        Random seed value (default: 42).
    """
    return _runtime_config.get('random_seed', _DEFAULT_CONFIG['random_seed'])

def get_memory_limit_mb() -> int:
    """
    Get the memory limit in megabytes for model inference.

    Returns:
        Memory limit in MB (default: 7000 for 7GB limit per SC-002).
    """
    return _runtime_config.get('memory_limit_mb', _DEFAULT_CONFIG['memory_limit_mb'])

def get_max_runtime_seconds() -> int:
    """
    Get the maximum allowed runtime in seconds.

    Returns:
        Maximum runtime (default: 86400 seconds = 24 hours per SC-001).
    """
    return _runtime_config.get('max_runtime_seconds', _DEFAULT_CONFIG['max_runtime_seconds'])

def get_min_valid_segments() -> int:
    """
    Get the minimum number of valid segments required.

    Returns:
        Minimum valid segments (default: 1000 per SC-003).
    """
    return _runtime_config.get('min_valid_segments', _DEFAULT_CONFIG['min_valid_segments'])

def get_correlation_method() -> str:
    """
    Get the correlation method for statistical analysis.

    Returns:
        Correlation method name (default: 'spearman').
    """
    return _runtime_config.get('correlation_method', _DEFAULT_CONFIG['correlation_method'])

def get_significance_threshold() -> float:
    """
    Get the significance threshold for statistical tests.

    Returns:
        P-value threshold (default: 0.05).
    """
    return _runtime_config.get('significance_threshold', _DEFAULT_CONFIG['significance_threshold'])

def get_figure_format() -> str:
    """
    Get the output format for visualization figures.

    Returns:
        Figure format string (default: 'png').
    """
    return _runtime_config.get('figure_format', _DEFAULT_CONFIG['figure_format'])

def get_figure_dpi() -> int:
    """
    Get the DPI setting for figure output.

    Returns:
        DPI value (default: 300 for publication quality).
    """
    return _runtime_config.get('figure_dpi', _DEFAULT_CONFIG['figure_dpi'])

def get_checksum_algorithm() -> str:
    """
    Get the checksum algorithm for artifact tracking.

    Returns:
        Checksum algorithm name (default: 'sha256').
    """
    return _runtime_config.get('checksum_algorithm', _DEFAULT_CONFIG['checksum_algorithm'])

def get_dataset_name() -> str:
    """
    Get the HuggingFace dataset name.

    Returns:
        Dataset identifier string.
    """
    return _runtime_config.get('dataset_name', _DEFAULT_CONFIG['dataset_name'])

def get_model_name() -> str:
    """
    Get the HuggingFace model name.

    Returns:
        Model identifier string.
    """
    return _runtime_config.get('model_name', _DEFAULT_CONFIG['model_name'])

def get_quantization_bits() -> int:
    """
    Get the quantization bit width for model loading.

    Returns:
        Quantization bits (default: 8 for 8-bit quantization).
    """
    return _runtime_config.get('quantization_bits', _DEFAULT_CONFIG['quantization_bits'])

def get_streaming_enabled() -> bool:
    """
    Get whether streaming mode is enabled for data loading.

    Returns:
        Boolean flag for streaming mode.
    """
    return _runtime_config.get('streaming_enabled', _DEFAULT_CONFIG['streaming_enabled'])

def get_pii_scan_enabled() -> bool:
    """
    Get whether PII scanning is enabled.

    Returns:
        Boolean flag for PII scanning (Constitution Principle III).
    """
    return _runtime_config.get('pii_scan_enabled', _DEFAULT_CONFIG['pii_scan_enabled'])

def get_all_config() -> Dict[str, Any]:
    """
    Get the complete configuration dictionary.

    Returns:
        Dictionary containing all configuration parameters.
    """
    config = _DEFAULT_CONFIG.copy()
    config.update(_runtime_config)
    return config

def set_config(key: str, value: Any) -> None:
    """
    Set a runtime configuration value.

    Args:
        key: Configuration parameter name.
        value: Configuration parameter value.
    """
    _runtime_config[key] = value

def reset_config() -> None:
    """Reset all configuration to defaults."""
    _runtime_config.clear()