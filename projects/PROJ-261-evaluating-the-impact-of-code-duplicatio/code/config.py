"""config.py
Minimal configuration utilities required by the tests and scripts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

_CONFIG: Dict[str, Any] = {
    "clone_thresholds": [0.7, 0.8, 0.9],
    "random_seed": 42,
    "memory_limit_mb": 7_000,
    "max_runtime_seconds": 3600,
    "min_valid_segments": 5,
    "correlation_method": "spearman",
    "significance_threshold": 0.05,
    "figure_format": "png",
    "figure_dpi": 300,
    "checksum_algorithm": "sha256",
    "dataset_name": "codeparrot/github-code",
    "model_name": "Salesforce/codegen-350M-mono",
    "quantization_bits": 8,
    "streaming_enabled": True,
    "pii_scan_enabled": True,
}

def get_all_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return dict(_CONFIG)

# Individual getters (kept for backward compatibility)
def get_clone_thresholds() -> list[float]:
    return _CONFIG["clone_thresholds"]

def get_random_seed() -> int:
    return _CONFIG["random_seed"]

def get_memory_limit_mb() -> int:
    return _CONFIG["memory_limit_mb"]

def get_max_runtime_seconds() -> int:
    return _CONFIG["max_runtime_seconds"]

def get_min_valid_segments() -> int:
    return _CONFIG["min_valid_segments"]

def get_correlation_method() -> str:
    return _CONFIG["correlation_method"]

def get_significance_threshold() -> float:
    return _CONFIG["significance_threshold"]

def get_figure_format() -> str:
    return _CONFIG["figure_format"]

def get_figure_dpi() -> int:
    return _CONFIG["figure_dpi"]

def get_checksum_algorithm() -> str:
    return _CONFIG["checksum_algorithm"]

def get_dataset_name() -> str:
    return _CONFIG["dataset_name"]

def get_model_name() -> str:
    return _CONFIG["model_name"]

def get_quantization_bits() -> int:
    return _CONFIG["quantization_bits"]

def get_streaming_enabled() -> bool:
    return _CONFIG["streaming_enabled"]

def get_pii_scan_enabled() -> bool:
    return _CONFIG["pii_scan_enabled"]