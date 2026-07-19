"""
Configuration management for the llmXive Drift Detection Pipeline.

This module centralizes project paths, random seed management, and runtime
parameters (batch sizes, thresholds) to ensure reproducibility and
consistent configuration across all pipeline stages.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# ========================================================================
# Project Root Configuration
# ========================================================================

# Determine the project root based on the file location.
# Assumes this file is at: projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CODE_DIR = _PROJECT_ROOT / "code"
_DATA_DIR = _PROJECT_ROOT / "data"
_DATA_RAW_DIR = _DATA_DIR / "raw"
_DATA_PROCESSED_DIR = _DATA_DIR / "processed"
_DATA_TEST_DIR = _DATA_DIR / "test"
_FIGURES_DIR = _PROJECT_ROOT / "figures"
_CONTRACTS_DIR = _PROJECT_ROOT / "contracts"

# Ensure these directories exist immediately upon import if they don't
# (Optional safety, but recommended for pipeline robustness)
_ROOT_DIRECTORIES = [
    _CODE_DIR,
    _DATA_DIR,
    _DATA_RAW_DIR,
    _DATA_PROCESSED_DIR,
    _DATA_TEST_DIR,
    _FIGURES_DIR,
    _CONTRACTS_DIR,
]

# ========================================================================
# Runtime Configuration State
# ========================================================================

# Global configuration dictionary for mutable runtime settings
_CONFIG: Dict[str, Any] = {
    "seed": 42,
    "batch_size": 32,
    "max_memory_gb": 7.0,
    "centroid_model": "all-MiniLM-L6-v2",
    "drift_threshold": 0.5,
    "annotation_top_percentile": 10,
    "annotation_bottom_percentile": 10,
    "kappa_threshold": 0.6,
    "max_retries": 3,
    "timeout_seconds": 300,
}

# ========================================================================
# Seed Management
# ========================================================================

def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across numpy, python random,
    and torch (if available).

    Args:
        seed (int): The integer seed value.
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
        # PyTorch is optional for this specific config module
        pass

# ========================================================================
# Path Helpers
# ========================================================================

def get_path(key: str) -> Path:
    """
    Resolves a logical key to an absolute Path within the project.

    Supported keys:
        - 'root', 'code', 'data', 'raw', 'processed', 'test', 'figures', 'contracts'
        - Specific filenames can be resolved if they are direct children of known dirs.

    Args:
        key (str): The logical identifier for the path.

    Returns:
        Path: The resolved absolute path.

    Raises:
        KeyError: If the key is not recognized.
    """
    key_map = {
        "root": _PROJECT_ROOT,
        "code": _CODE_DIR,
        "data": _DATA_DIR,
        "raw": _DATA_RAW_DIR,
        "processed": _DATA_PROCESSED_DIR,
        "test": _DATA_TEST_DIR,
        "figures": _FIGURES_DIR,
        "contracts": _CONTRACTS_DIR,
    }

    if key in key_map:
        return key_map[key]

    # Fallback: treat as filename relative to root if not found
    # This allows dynamic construction like get_path("data/raw/taxonomy.json")
    # But strictly, we prefer the explicit keys above.
    # If a specific file path is requested that isn't in the map,
    # we construct it relative to root.
    return _PROJECT_ROOT / key

def get_output_path(subdir: str, filename: str) -> Path:
    """
    Constructs a path for an output file in a specific subdirectory.

    Args:
        subdir (str): The subdirectory name (e.g., 'processed', 'raw').
        filename (str): The name of the file.

    Returns:
        Path: The full path to the file.
    """
    base = get_path(subdir)
    return base / filename

def ensure_directories() -> None:
    """
    Creates all required project directories if they do not exist.
    """
    for dir_path in _ROOT_DIRECTORIES:
        dir_path.mkdir(parents=True, exist_ok=True)

# ========================================================================
# Configuration Accessors
# ========================================================================

def get_config(key: str, default: Any = None) -> Any:
    """
    Retrieves a configuration value.

    Args:
        key (str): The configuration key.
        default (Any): Default value if key is missing.

    Returns:
        Any: The configuration value.
    """
    return _CONFIG.get(key, default)

def update_config(updates: Dict[str, Any]) -> None:
    """
    Updates multiple configuration values at once.

    Args:
        updates (Dict[str, Any]): Dictionary of key-value pairs to update.
    """
    _CONFIG.update(updates)

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a read-only copy of the current configuration state.

    Returns:
        Dict[str, Any]: The current configuration dictionary.
    """
    return _CONFIG.copy()

# ========================================================================
# Specific Accessors for Common Parameters
# ========================================================================

def get_batch_size() -> int:
    """Returns the current batch size."""
    return _CONFIG["batch_size"]

def get_max_memory_gb() -> float:
    """Returns the maximum allowed memory in GB."""
    return _CONFIG["max_memory_gb"]

def get_drift_threshold() -> float:
    """Returns the drift score threshold for flagging."""
    return _CONFIG["drift_threshold"]

def get_centroid_model() -> str:
    """Returns the model name for centroid generation."""
    return _CONFIG["centroid_model"]

# Initialize directories on import to ensure structure exists
ensure_directories()

# Set default seed
set_seed(_CONFIG["seed"])