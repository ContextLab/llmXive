"""
Configuration management for llmXive Drift Detection Pipeline.

This module handles random seeds, file paths, batch sizes, and other
hyperparameters required for reproducibility and resource management.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = {
    "seed": 42,
    "batch_size": 32,
    "max_memory_gb": 7,
    "drift_threshold": 1.5,
    "centroid_model": "all-MiniLM-L6-v2",
    "max_workers": 4,
    "log_level": "INFO",
    "paths": {
        "raw": "data/raw",
        "processed": "data/processed",
        "test": "data/test",
        "specs": "specs/001-llmxive-drift-detection",
        "docs": "docs",
        "checksums": "data/checksums.json",
        "taxonomy_owasp": "data/raw/taxonomy_owasp.json",
        "taxonomy_agentdog": "data/raw/taxonomy_agentdog.json",
        "taxonomy_centroids": "data/processed/taxonomy_centroids.json",
        "drift_scores": "data/processed/drift_scores.csv",
        "ground_truth": "data/test/real_ground_truth_fixture.json",
        "validation_stats": "data/processed/validation_stats.json",
        "us01_stats": "data/processed/us01_final_stats.json",
    }
}


def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: Integer seed value.
    """
    _CONFIG["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return _CONFIG.copy()


def update_config(key: str, value: Any) -> None:
    """
    Update a specific configuration value.
    
    Args:
        key: Configuration key (supports dot notation for nested keys, e.g., 'paths.raw').
        value: New value to set.
    """
    if '.' in key:
        parts = key.split('.')
        current = _CONFIG
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    else:
        _CONFIG[key] = value


def get_config_summary() -> str:
    """Return a human-readable summary of the current configuration."""
    return (
        f"Seed: {_CONFIG['seed']}\n"
        f"Batch Size: {_CONFIG['batch_size']}\n"
        f"Max Memory (GB): {_CONFIG['max_memory_gb']}\n"
        f"Drift Threshold: {_CONFIG['drift_threshold']}\n"
        f"Centroid Model: {_CONFIG['centroid_model']}\n"
        f"Log Level: {_CONFIG['log_level']}"
    )


def get_path(relative_path: Optional[str] = None) -> Path:
    """
    Resolve a path relative to the project root or a specific config path.
    
    Args:
        relative_path: Optional relative path string. If None, returns project root.
                       If a key from _CONFIG['paths'] is provided, resolves that.
    
    Returns:
        Absolute Path object.
    """
    if relative_path is None:
        return _PROJECT_ROOT
    
    # Check if it's a named path in config
    if relative_path in _CONFIG.get("paths", {}):
        base = _CONFIG["paths"][relative_path]
        return _PROJECT_ROOT / base
    
    # Otherwise treat as a relative string
    return _PROJECT_ROOT / relative_path


def get_output_path(output_name: str, category: Optional[str] = None) -> Path:
    """
    Construct an output path based on category (raw, processed, test) or default to processed.
    
    Args:
        output_name: Filename.
        category: One of 'raw', 'processed', 'test', or None (defaults to 'processed').
    
    Returns:
        Absolute Path object for the output file.
    """
    if category is None:
        category = "processed"
    
    base_dir = get_path(category)
    return base_dir / output_name


def ensure_directories(paths: Optional[list] = None) -> None:
    """
    Ensure that all required directories exist.
    
    Args:
        paths: Optional list of relative path strings to ensure. If None, ensures all configured paths.
    """
    dirs_to_create = paths if paths else list(_CONFIG.get("paths", {}).values())
    
    for dir_str in dirs_to_create:
        target_path = _PROJECT_ROOT / dir_str
        target_path.mkdir(parents=True, exist_ok=True)


def get_batch_size() -> int:
    """Return the configured batch size."""
    return _CONFIG["batch_size"]


def get_max_memory_gb() -> int:
    """Return the configured maximum memory limit in GB."""
    return _CONFIG["max_memory_gb"]


def get_drift_threshold() -> float:
    """Return the configured drift threshold."""
    return _CONFIG["drift_threshold"]


def get_centroid_model() -> str:
    """Return the configured centroid model name."""
    return _CONFIG["centroid_model"]