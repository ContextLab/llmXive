"""
Configuration management for the llmXive AgentDoG drift detection pipeline.

Handles random seeds, file paths, batch sizes, and memory limits.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# Project Root (assumed to be the parent of the 'code' directory)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = {
    "seed": 42,
    "batch_size": 32,
    "max_memory_gb": 7,
    "drift_threshold": 1.5,
    "centroid_model": "all-MiniLM-L6-v2",
    "data_dir": "data",
    "code_dir": "code",
    "test_dir": "tests",
    "specs_dir": "specs",
    "docs_dir": "docs",
    "raw_data_dir": "data/raw",
    "processed_data_dir": "data/processed",
    "test_data_dir": "data/test",
    "figures_dir": "figures",
}

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The integer seed value. Defaults to _CONFIG['seed'] if None.
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
        pass  # torch not installed, ignore

def get_config() -> Dict[str, Any]:
    """Return a copy of the current configuration dictionary."""
    return _CONFIG.copy()

def update_config(updates: Dict[str, Any]) -> None:
    """
    Update the global configuration with provided key-value pairs.
    
    Args:
        updates: Dictionary of configuration overrides.
    """
    _CONFIG.update(updates)

def get_path(key: str) -> Path:
    """
    Resolve a project-relative path based on the configuration key.
    
    Args:
        key: The key in _CONFIG corresponding to a relative path.
    
    Returns:
        Absolute Path object.
    
    Raises:
        KeyError: If the key is not found in configuration.
    """
    if key not in _CONFIG:
        raise KeyError(f"Configuration key '{key}' not found.")
    
    relative_path = _CONFIG[key]
    return _PROJECT_ROOT / relative_path

def get_output_path(filename: str, subdir: Optional[str] = None) -> Path:
    """
    Construct a path for an output file within the processed data directory.
    
    Args:
        filename: The name of the file.
        subdir: Optional subdirectory within the processed data dir.
    
    Returns:
        Absolute Path object for the output file.
    """
    base = get_path("processed_data_dir")
    if subdir:
        base = base / subdir
    return base / filename

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

def ensure_directories() -> None:
    """Create all directories defined in the configuration if they don't exist."""
    dirs_to_create = [
        "data_dir",
        "code_dir",
        "test_dir",
        "specs_dir",
        "docs_dir",
        "raw_data_dir",
        "processed_data_dir",
        "test_data_dir",
        "figures_dir",
    ]
    for key in dirs_to_create:
        path = get_path(key)
        path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> str:
    """Return a string summary of the current configuration for logging."""
    summary_lines = [
        "--- Configuration Summary ---",
        f"Seed: {_CONFIG['seed']}",
        f"Batch Size: {_CONFIG['batch_size']}",
        f"Max Memory (GB): {_CONFIG['max_memory_gb']}",
        f"Drift Threshold: {_CONFIG['drift_threshold']}",
        f"Centroid Model: {_CONFIG['centroid_model']}",
        f"Project Root: {_PROJECT_ROOT}",
    ]
    return "\n".join(summary_lines)