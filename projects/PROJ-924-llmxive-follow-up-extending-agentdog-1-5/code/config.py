"""
Configuration management for the llmXive drift detection pipeline.

This module handles random seeds, path management, batch sizes, and
memory constraints for the project.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# --- Project Constants ---
# Root directory of the project
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# Relative path to the project directory
_PROJECT_DIR = _PROJECT_ROOT / "projects" / "PROJ-924-llmxive-follow-up-extending-agentdog-1-5"

# --- Configuration Defaults ---
# Random seed for reproducibility (Requirement: 42)
RANDOM_SEED = 42
# Maximum RAM in GB (Requirement: 7)
MAX_RAM_GB = 7
# Batch size for processing (Requirement: 64)
BATCH_SIZE = 64

# --- Internal State ---
_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "project_root": _PROJECT_ROOT,
    "project_dir": _PROJECT_DIR,
    "data_raw_dir": _PROJECT_DIR / "data" / "raw",
    "data_processed_dir": _PROJECT_DIR / "data" / "processed",
    "data_test_dir": _PROJECT_DIR / "data" / "test",
    "specs_dir": _PROJECT_DIR / "specs",
    "docs_dir": _PROJECT_DIR / "docs",
    "code_dir": _PROJECT_DIR / "code",
    "drift_detection_specs_dir": _PROJECT_DIR / "specs" / "001-llmxive-drift-detection",
    # Model configurations
    "centroid_model": "all-MiniLM-L6-v2",
    "baseline_model": "google/flan-t5-small",
    # Drift detection parameters
    "drift_threshold": 0.5,
}

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for Python, NumPy, and the global config.
    
    Args:
        seed: The seed value. Defaults to RANDOM_SEED (42).
    """
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed)
    np.random.seed(seed)
    _config["random_seed"] = seed

def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return _config.copy()

def update_config(new_values: Dict[str, Any]) -> None:
    """
    Update the configuration with new values.
    
    Args:
        new_values: Dictionary of key-value pairs to update.
    """
    _config.update(new_values)

def get_config_summary() -> str:
    """Return a string summary of the current configuration."""
    return (
        f"Seed: {_config['random_seed']}, "
        f"Max RAM: {_config['max_ram_gb']}GB, "
        f"Batch Size: {_config['batch_size']}"
    )

def get_path(key: str) -> Path:
    """
    Retrieve a path from the configuration by key.
    
    Args:
        key: The configuration key (e.g., 'data_raw_dir').
        
    Returns:
        The corresponding Path object.
        
    Raises:
        KeyError: If the key does not exist in the configuration.
    """
    if key not in _config:
        raise KeyError(f"Configuration key '{key}' not found.")
    return _config[key]

def get_output_path(filename: str, sub_dir: str = "processed") -> Path:
    """
    Construct a full output path for a file.
    
    Args:
        filename: The name of the file.
        sub_dir: The subdirectory within the data directory (default: 'processed').
        
    Returns:
        The full Path to the file.
    """
    base_dir = _config.get(f"data_{sub_dir}_dir", _config["data_processed_dir"])
    return base_dir / filename

def ensure_directories() -> None:
    """
    Ensure all directories defined in the configuration exist.
    Creates them if they do not exist.
    """
    dir_keys = [
        "project_root", "project_dir", "data_raw_dir", 
        "data_processed_dir", "data_test_dir", "specs_dir", 
        "docs_dir", "code_dir", "drift_detection_specs_dir"
    ]
    for key in dir_keys:
        if key in _config:
            path = _config[key]
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)

def get_batch_size() -> int:
    """Return the configured batch size."""
    return _config["batch_size"]

def get_max_memory_gb() -> int:
    """Return the configured maximum RAM in GB."""
    return _config["max_ram_gb"]

def get_drift_threshold() -> float:
    """Return the configured drift threshold."""
    return _config["drift_threshold"]

def get_centroid_model() -> str:
    """Return the configured centroid model name."""
    return _config["centroid_model"]

def get_baseline_model() -> str:
    """Return the configured baseline model name."""
    return _config["baseline_model"]
