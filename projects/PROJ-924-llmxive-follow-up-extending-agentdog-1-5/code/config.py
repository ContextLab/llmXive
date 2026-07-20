"""
Configuration management for llmXive automated science pipeline.

Handles random seeds, path resolution, batch sizes, and memory limits.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

# Project Root
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_CONFIG: Dict[str, Any] = {
    "seed": 42,
    "batch_size": 32,
    "max_memory_gb": 7,
    "drift_threshold": 0.5,
    "centroid_model": "all-MiniLM-L6-v2",
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_test": "data/test",
        "specs": "specs",
        "docs": "docs",
        "code": "code",
        "tests": "tests"
    }
}

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across numpy, python random, and torch (if available).
    
    Args:
        seed: Integer seed value.
    """
    if seed is None:
        seed = _CONFIG["seed"]
    
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
        key: Configuration key (e.g., 'batch_size', 'seed').
        value: New value to set.
    """
    if key in _CONFIG:
        _CONFIG[key] = value
    else:
        # Allow dynamic keys if needed, but warn in production
        _CONFIG[key] = value

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "seed": _CONFIG["seed"],
        "batch_size": _CONFIG["batch_size"],
        "max_memory_gb": _CONFIG["max_memory_gb"],
        "drift_threshold": _CONFIG["drift_threshold"],
        "centroid_model": _CONFIG["centroid_model"]
    }

def get_path(path_type: str) -> Path:
    """
    Resolve a project-relative path to an absolute Path object.
    
    Args:
        path_type: Key in _CONFIG['paths'] (e.g., 'data_raw', 'specs').
        
    Returns:
        Absolute Path object.
        
    Raises:
        KeyError: If path_type is not found in configuration.
    """
    if path_type not in _CONFIG["paths"]:
        raise KeyError(f"Path type '{path_type}' not found in configuration.")
    return _PROJECT_ROOT / _CONFIG["paths"][path_type]

def get_output_path(path_type: str, filename: str) -> Path:
    """
    Resolve a full output path including filename.
    
    Args:
        path_type: Key in _CONFIG['paths'].
        filename: Name of the file.
        
    Returns:
        Absolute Path object to the file.
    """
    base_dir = get_path(path_type)
    return base_dir / filename

def ensure_directories() -> None:
    """Create all configured directories if they do not exist."""
    for path_key in _CONFIG["paths"].values():
        full_path = _PROJECT_ROOT / path_key
        full_path.mkdir(parents=True, exist_ok=True)

def get_batch_size() -> int:
    """Return the configured batch size."""
    return _CONFIG["batch_size"]

def get_max_memory_gb() -> int:
    """Return the configured maximum memory limit in GB."""
    return _CONFIG["max_memory_gb"]

def get_drift_threshold() -> float:
    """Return the configured drift score threshold."""
    return _CONFIG["drift_threshold"]

def get_centroid_model() -> str:
    """Return the configured centroid model name."""
    return _CONFIG["centroid_model"]