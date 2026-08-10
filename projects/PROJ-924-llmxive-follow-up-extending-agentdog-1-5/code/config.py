"""
Configuration management for the AgentDoG Drift Detection pipeline.

Handles random seeds, memory constraints, batch sizes, and path resolution.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# --- Core Constants ---
RANDOM_SEED = 42
MAX_RAM_GB = 7
# Batch size reference: arxiv.org/abs/2410.21676
BATCH_SIZE = 64 

# --- Project Paths ---
# Assuming the project root is the parent of the 'code' directory
# or we can infer it from the current working directory if run as a script.
# For robustness, we define relative paths from the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_ROOT = _PROJECT_ROOT / "data"
_DATA_RAW = _DATA_ROOT / "raw"
_DATA_PROCESSED = _DATA_ROOT / "processed"
_DATA_TEST = _DATA_ROOT / "test"
_CODE_ROOT = _PROJECT_ROOT / "code"
_SPEC_ROOT = _PROJECT_ROOT / "specs"
_DOCS_ROOT = _PROJECT_ROOT / "docs"

# --- Global Config State ---
_config: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": BATCH_SIZE,
    "drift_threshold": 0.5,
    "centroid_model": "all-MiniLM-L6-v2",
    "baseline_model": "google/flan-t5-small",
    "paths": {
        "raw": str(_DATA_RAW),
        "processed": str(_DATA_PROCESSED),
        "test": str(_DATA_TEST),
        "code": str(_CODE_ROOT),
        "specs": str(_SPEC_ROOT),
        "docs": str(_DOCS_ROOT),
        "root": str(_PROJECT_ROOT),
    }
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
        pass
    
    _config["random_seed"] = seed

def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return _config.copy()

def update_config(key: str, value: Any) -> None:
    """Update a specific configuration value."""
    if key in _config:
        _config[key] = value
    elif key in _config["paths"]:
        _config["paths"][key] = value
    else:
        # Allow adding new top-level keys if not predefined
        _config[key] = value

def get_config_summary() -> str:
    """Return a human-readable summary of the current configuration."""
    return (
        f"Seed: {_config['random_seed']}, "
        f"Max RAM: {_config['max_ram_gb']}GB, "
        f"Batch Size: {_config['batch_size']}, "
        f"Centroid Model: {_config['centroid_model']}, "
        f"Baseline Model: {_config['baseline_model']}"
    )

def get_path(name: str) -> Path:
    """
    Retrieve a path from the configuration.
    
    Args:
        name: The key of the path (e.g., 'raw', 'processed', 'root').
    
    Returns:
        The Path object corresponding to the key.
    
    Raises:
        KeyError: If the path name is not found in configuration.
    """
    if name in _config["paths"]:
        return Path(_config["paths"][name])
    raise KeyError(f"Path '{name}' not found in configuration.")

def get_output_path(subdir: str, filename: str) -> Path:
    """
    Construct a full output path within the processed directory.
    
    Args:
        subdir: Subdirectory name (e.g., 'drift_results').
        filename: The file name.
    
    Returns:
        Full Path to the output file.
    """
    base = get_path("processed")
    return base / subdir / filename

def ensure_directories() -> None:
    """
    Ensure all directories defined in the configuration exist.
    Creates them if they are missing.
    """
    for path_str in _config["paths"].values():
        path = Path(path_str)
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
