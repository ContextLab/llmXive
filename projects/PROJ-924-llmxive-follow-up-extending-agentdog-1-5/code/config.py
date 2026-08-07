"""
Configuration management for llmXive Drift Detection Pipeline.

This module centralizes project constants, random seed management,
path resolution, and runtime parameters to ensure reproducibility
and consistent behavior across the pipeline.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List
import numpy as np

# ==============================================================================
# Core Constants (Acceptance Criteria)
# ==============================================================================
RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64

# ==============================================================================
# Derived Constants & Defaults
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TEST_DATA_DIR = DATA_DIR / "test"
SPECS_DIR = PROJECT_ROOT / "specs"
DOCS_DIR = PROJECT_ROOT / "docs"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Drift Detection Specifics
DRIFT_THRESHOLD = 0.5
CENTROID_MODEL_NAME = "all-MiniLM-L6-v2"
BASELINE_MODEL_NAME = "google/flan-t5-small"

# ==============================================================================
# Global State
# ==============================================================================
_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "project_root": PROJECT_ROOT,
    "data_dir": DATA_DIR,
    "raw_data_dir": RAW_DATA_DIR,
    "processed_data_dir": PROCESSED_DATA_DIR,
    "test_data_dir": TEST_DATA_DIR,
    "specs_dir": SPECS_DIR,
    "docs_dir": DOCS_DIR,
    "code_dir": CODE_DIR,
    "tests_dir": TESTS_DIR,
    "drift_threshold": DRIFT_THRESHOLD,
    "centroid_model": CENTROID_MODEL_NAME,
    "baseline_model": BASELINE_MODEL_NAME,
}


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The seed value. Defaults to RANDOM_SEED if None.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed, skip GPU seeding


def get_config() -> Dict[str, Any]:
    """
    Return a copy of the current configuration dictionary.
    
    Returns:
        Dict containing all configuration parameters.
    """
    return _config.copy()


def update_config(key: str, value: Any) -> None:
    """
    Update a specific configuration parameter.
    
    Args:
        key: The configuration key to update.
        value: The new value.
        
    Raises:
        KeyError: If the key is not recognized in the default config.
    """
    if key not in _config:
        raise KeyError(f"Configuration key '{key}' not found. Use update_config to add new keys manually if necessary, or modify _config directly.")
    _config[key] = value


def get_config_summary() -> str:
    """
    Generate a human-readable summary of the current configuration.
    
    Returns:
        String summary of key parameters.
    """
    return (
        f"Random Seed: {_config['random_seed']}\n"
        f"Max RAM (GB): {_config['max_ram_gb']}\n"
        f"Batch Size: {_config['batch_size']}\n"
        f"Drift Threshold: {_config['drift_threshold']}\n"
        f"Centroid Model: {_config['centroid_model']}\n"
        f"Baseline Model: {_config['baseline_model']}"
    )


def get_path(key: str) -> Path:
    """
    Resolve a path based on a configuration key.
    
    Args:
        key: The configuration key (e.g., 'data_dir', 'raw_data_dir').
        
    Returns:
        Resolved Path object.
        
    Raises:
        KeyError: If the key does not exist or does not map to a Path.
    """
    if key not in _config:
        raise KeyError(f"Path key '{key}' not found in config.")
    val = _config[key]
    if isinstance(val, Path):
        return val
    # Handle string paths if necessary
    return Path(val)


def get_output_path(subdir: str, filename: str) -> Path:
    """
    Construct a full output path within the processed data directory.
    
    Args:
        subdir: Subdirectory within processed data (e.g., 'batches').
        filename: The name of the file.
        
    Returns:
        Full Path to the output file.
    """
    return _config["processed_data_dir"] / subdir / filename


def ensure_directories(paths: Optional[List[Path]] = None) -> None:
    """
    Ensure that the specified directories exist. Creates them if missing.
    
    Args:
        paths: List of Path objects. If None, defaults to standard project directories.
    """
    if paths is None:
        paths = [
            _config["data_dir"],
            _config["raw_data_dir"],
            _config["processed_data_dir"],
            _config["test_data_dir"],
            _config["specs_dir"],
            _config["docs_dir"],
            _config["code_dir"],
            _config["tests_dir"],
        ]
    
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def get_batch_size() -> int:
    """
    Get the current batch size.
    
    Returns:
        Integer batch size.
    """
    return _config["batch_size"]


def get_max_memory_gb() -> float:
    """
    Get the maximum allowed RAM in GB.
    
    Returns:
        Float max RAM.
    """
    return _config["max_ram_gb"]


def get_drift_threshold() -> float:
    """
    Get the default drift threshold.
    
    Returns:
        Float drift threshold.
    """
    return _config["drift_threshold"]


def get_centroid_model() -> str:
    """
    Get the model name for centroid generation.
    
    Returns:
        String model name.
    """
    return _config["centroid_model"]


def get_baseline_model() -> str:
    """
    Get the model name for baseline comparison.
    
    Returns:
        String model name.
    """
    return _config["baseline_model"]
