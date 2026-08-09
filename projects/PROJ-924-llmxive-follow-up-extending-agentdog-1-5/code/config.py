"""
Configuration management for the llmXive Drift Detection pipeline.

This module centralizes random seeds, path configurations, and batch sizes
to ensure reproducibility and consistent resource management across the project.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# --- Core Constants ---
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64

# --- Project Paths ---
# Base directory is the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Internal State ---
_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "project_root": _PROJECT_ROOT,
    "data_raw_dir": _PROJECT_ROOT / "data" / "raw",
    "data_processed_dir": _PROJECT_ROOT / "data" / "processed",
    "data_test_dir": _PROJECT_ROOT / "data" / "test",
    "code_dir": _PROJECT_ROOT / "code",
    "specs_dir": _PROJECT_ROOT / "specs",
    "docs_dir": _PROJECT_ROOT / "docs",
}


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across numpy, python random, and torch (if available).
    
    Args:
        seed: The seed value. Defaults to RANDOM_SEED if None.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Update internal config
    _config["random_seed"] = seed
    
    # Attempt to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration dictionary.
    
    Returns:
        A copy of the current configuration.
    """
    return _config.copy()


def update_config(key: str, value: Any) -> None:
    """
    Update a specific configuration value.
    
    Args:
        key: The configuration key to update.
        value: The new value.
    """
    _config[key] = value


def get_config_summary() -> str:
    """
    Get a human-readable summary of the configuration.
    
    Returns:
        A string containing key configuration values.
    """
    return (
        f"Random Seed: {_config['random_seed']}\n"
        f"Max RAM (GB): {_config['max_ram_gb']}\n"
        f"Batch Size: {_config['batch_size']}\n"
        f"Project Root: {_config['project_root']}"
    )


def get_path(relative_path: Optional[str] = None) -> Path:
    """
    Resolve a path relative to the project root or a specific directory.
    
    Args:
        relative_path: Optional relative path string. If None, returns project root.
        
    Returns:
        A resolved Path object.
    """
    if relative_path is None:
        return _config["project_root"]
    
    return _config["project_root"] / relative_path


def get_output_path(output_type: str, filename: str) -> Path:
    """
    Get the output path for a specific type of artifact.
    
    Args:
        output_type: Type of output (e.g., 'raw', 'processed', 'test').
        filename: Name of the file.
        
    Returns:
        Resolved Path to the output file.
        
    Raises:
        ValueError: If the output_type is not recognized.
    """
    path_map = {
        "raw": _config["data_raw_dir"],
        "processed": _config["data_processed_dir"],
        "test": _config["data_test_dir"],
    }
    
    if output_type not in path_map:
        raise ValueError(f"Unknown output type: {output_type}. Valid types: {list(path_map.keys())}")
        
    return path_map[output_type] / filename


def ensure_directories() -> None:
    """
    Ensure all required directories exist in the project structure.
    Creates them if they do not exist.
    """
    dirs_to_create = [
        _config["data_raw_dir"],
        _config["data_processed_dir"],
        _config["data_test_dir"],
        _config["code_dir"],
        _config["specs_dir"],
        _config["docs_dir"],
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_batch_size() -> int:
    """
    Get the configured batch size.
    
    Returns:
        The batch size integer.
    """
    return _config["batch_size"]


def get_max_memory_gb() -> int:
    """
    Get the configured maximum RAM in GB.
    
    Returns:
        The max RAM integer.
    """
    return _config["max_ram_gb"]


def get_drift_threshold() -> float:
    """
    Get the default drift threshold.
    
    Returns:
        The drift threshold float.
    """
    return 0.8


def get_centroid_model() -> str:
    """
    Get the default centroid model name.
    
    Returns:
        The model name string.
    """
    return "sentence-transformers/all-MiniLM-L6-v2"


def get_baseline_model() -> str:
    """
    Get the default baseline model name.
    
    Returns:
        The model name string.
    """
    return "google/flan-t5-small"
