"""
Configuration management for the llmXive drift detection pipeline.

This module provides centralized configuration handling including:
- Random seed management
- Path resolution
- Batch size and memory limits
- Model selection
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np


# Default configuration values
_config = {
    "RANDOM_SEED": 42,
    "MAX_RAM_GB": 7,
    "BATCH_SIZE": 64,
    "PROJECT_ROOT": None,
    "DRIFT_THRESHOLD": 0.5,
    "CENTROID_MODEL": "all-MiniLM-L6-v2",
    "BASELINE_MODEL": "facebook/bart-large-mnli",
}


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility.
    
    Args:
        seed: Random seed value. Uses _config["RANDOM_SEED"] if None.
    """
    if seed is None:
        seed = _config["RANDOM_SEED"]
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration dictionary.
    
    Returns:
        Dictionary containing all configuration values.
    """
    return _config.copy()


def update_config(key: str, value: Any) -> None:
    """
    Update a configuration value.
    
    Args:
        key: Configuration key.
        value: New value.
    """
    _config[key] = value


def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    
    Returns:
        Dictionary with key configuration values for logging.
    """
    return {
        "random_seed": _config["RANDOM_SEED"],
        "max_ram_gb": _config["MAX_RAM_GB"],
        "batch_size": _config["BATCH_SIZE"],
        "drift_threshold": _config["DRIFT_THRESHOLD"],
        "centroid_model": _config["CENTROID_MODEL"],
        "baseline_model": _config["BASELINE_MODEL"],
    }


def get_path(relative_path: str) -> Path:
    """
    Get an absolute path relative to the project root.
    
    Args:
        relative_path: Path relative to project root.
        
    Returns:
        Absolute Path object.
    """
    if _config["PROJECT_ROOT"] is None:
        # Default to parent of code directory if not set
        _config["PROJECT_ROOT"] = Path(__file__).parent.parent
    
    return Path(_config["PROJECT_ROOT"]) / relative_path


def get_output_path(relative_path: str) -> Path:
    """
    Get an output path, ensuring the directory exists.
    
    Args:
        relative_path: Path relative to project root.
        
    Returns:
        Absolute Path object with parent directories created.
    """
    path = get_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ensure_directories(paths: List[str]) -> None:
    """
    Ensure that the specified directories exist.
    
    Args:
        paths: List of relative paths to ensure exist.
    """
    for path_str in paths:
        path = get_path(path_str)
        path.mkdir(parents=True, exist_ok=True)


def get_batch_size() -> int:
    """
    Get the batch size for processing.
    
    Returns:
        Batch size integer.
    """
    return _config["BATCH_SIZE"]


def get_max_memory_gb() -> int:
    """
    Get the maximum memory limit in GB.
    
    Returns:
        Maximum RAM in GB.
    """
    return _config["MAX_RAM_GB"]


def get_drift_threshold() -> float:
    """
    Get the drift threshold for flagging.
    
    Returns:
        Drift threshold value.
    """
    return _config["DRIFT_THRESHOLD"]


def get_centroid_model() -> str:
    """
    Get the model name for centroid embedding generation.
    
    Returns:
        Model name string.
    """
    return _config["CENTROID_MODEL"]


def get_baseline_model() -> str:
    """
    Get the model name for baseline classification.
    
    Returns:
        Model name string.
    """
    return _config["BASELINE_MODEL"]


# Initialize project root if not set
if _config["PROJECT_ROOT"] is None:
    _config["PROJECT_ROOT"] = Path(__file__).parent.parent
