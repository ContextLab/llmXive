"""
Configuration management for the llmXive automated science pipeline.
Manages random seeds, paths, batch sizes, and model parameters.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# Project root directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default configuration values
_DEFAULT_CONFIG: Dict[str, Any] = {
    "random_seed": 42,
    "batch_size": 32,
    "max_memory_gb": 7.0,
    "drift_threshold": 0.5,
    "centroid_model": "all-MiniLM-L6-v2",
    "baseline_model": "facebook/bart-large-mnli",
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_test": "data/test",
        "data_checksums": "data/checksums.json",
        "specs": "specs/001-llmxive-drift-detection",
        "figures": "figures",
        "outputs": "data/processed",
    },
}

_current_config: Dict[str, Any] = _DEFAULT_CONFIG.copy()


def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across numpy, random, and torch (if available).

    Args:
        seed: The random seed value to use.
    """
    _current_config["random_seed"] = seed
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
    """
    Get the current configuration dictionary.

    Returns:
        A copy of the current configuration dictionary.
    """
    return _current_config.copy()


def update_config(updates: Dict[str, Any]) -> None:
    """
    Update the configuration with new values.

    Args:
        updates: A dictionary of configuration updates.
    """
    def _deep_update(base: Dict, updates: Dict) -> None:
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                _deep_update(base[key], value)
            else:
                base[key] = value

    _deep_update(_current_config, updates)


def get_config_summary() -> str:
    """
    Get a human-readable summary of the current configuration.

    Returns:
        A string containing key configuration values.
    """
    return (
        f"Random Seed: {_current_config['random_seed']}\n"
        f"Batch Size: {_current_config['batch_size']}\n"
        f"Max Memory (GB): {_current_config['max_memory_gb']}\n"
        f"Drift Threshold: {_current_config['drift_threshold']}\n"
        f"Centroid Model: {_current_config['centroid_model']}\n"
        f"Baseline Model: {_current_config['baseline_model']}"
    )


def get_path(key: str, *subpaths: str) -> Path:
    """
    Resolve a path from the configuration.

    Args:
        key: The configuration key for the base path (e.g., 'data_raw').
        subpaths: Optional subpaths to append to the base path.

    Returns:
        A Path object pointing to the resolved location.

    Raises:
        KeyError: If the key is not found in the paths configuration.
    """
    paths = _current_config.get("paths", {})
    if key not in paths:
        raise KeyError(f"Path key '{key}' not found in configuration. Available keys: {list(paths.keys())}")

    base = _PROJECT_ROOT / paths[key]
    return base.joinpath(*subpaths) if subpaths else base


def get_output_path(filename: str, subdirectory: Optional[str] = None) -> Path:
    """
    Get a path for output files in the processed data directory.

    Args:
        filename: The name of the output file.
        subdirectory: Optional subdirectory within the outputs path.

    Returns:
        A Path object pointing to the output location.
    """
    if subdirectory:
        return _PROJECT_ROOT / _current_config["paths"]["data_processed"] / subdirectory / filename
    return _PROJECT_ROOT / _current_config["paths"]["data_processed"] / filename


def ensure_directories(paths: List[str]) -> None:
    """
    Ensure that the specified directories exist.

    Args:
        paths: List of configuration keys representing directory paths to create.
    """
    for path_key in paths:
        dir_path = get_path(path_key)
        dir_path.mkdir(parents=True, exist_ok=True)


def get_batch_size() -> int:
    """
    Get the configured batch size.

    Returns:
        The batch size integer.
    """
    return _current_config["batch_size"]


def get_max_memory_gb() -> float:
    """
    Get the configured maximum memory limit in GB.

    Returns:
        The memory limit as a float.
    """
    return _current_config["max_memory_gb"]


def get_drift_threshold() -> float:
    """
    Get the configured drift threshold.

    Returns:
        The drift threshold float.
    """
    return _current_config["drift_threshold"]


def get_centroid_model() -> str:
    """
    Get the configured centroid model name.

    Returns:
        The model name string.
    """
    return _current_config["centroid_model"]


def get_baseline_model() -> str:
    """
    Get the configured baseline model name.

    Returns:
        The model name string.
    """
    return _current_config["baseline_model"]


if __name__ == "__main__":
    # Example usage / self-test
    print("llmXive Configuration Module")
    print("=" * 40)
    print(get_config_summary())
    print("=" * 40)
    print("Testing path resolution...")
    print(f"Data Raw Path: {get_path('data_raw')}")
    print(f"Output Path: {get_output_path('test.csv', 'subdir')}")
    print("Directories check...")
    ensure_directories(["data_raw", "data_processed", "data_test"])
    print("Configuration module ready.")