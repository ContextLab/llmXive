import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# Project Root Configuration
# This script assumes it is run from the project root or that the environment
# is set up such that the project root is discoverable.
# For robustness, we define the project root relative to this file's location.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_NAME = "PROJ-924-llmxive-follow-up-extending-agentdog-1-5"

# Ensure the project root matches expectations if this file is moved
if _PROJECT_ROOT.name != _PROJECT_NAME:
    # Fallback: try to find the project root by walking up
    _current = _PROJECT_ROOT
    while _current.parent != _current and _current.name != _PROJECT_NAME:
        _current = _current.parent
    if _current.name == _PROJECT_NAME:
        _PROJECT_ROOT = _current
    else:
        # If we can't find it, we assume the current working directory is the root
        # or that the user has set the PROJECT_ROOT env var
        _PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "."))

# Standard Directory Structure
_DIRS = {
    "root": _PROJECT_ROOT,
    "code": _PROJECT_ROOT / "code",
    "data": _PROJECT_ROOT / "data",
    "data_raw": _PROJECT_ROOT / "data" / "raw",
    "data_processed": _PROJECT_ROOT / "data" / "processed",
    "data_test": _PROJECT_ROOT / "data" / "test",
    "tests": _PROJECT_ROOT / "tests",
    "docs": _PROJECT_ROOT / "docs",
    "contracts": _PROJECT_ROOT / "contracts",
    "figures": _PROJECT_ROOT / "figures",
}

# Default Configuration Values
DEFAULT_CONFIG = {
    "seed": 42,
    "batch_size": 32,
    "max_logs": None,  # None means no limit
    "embedding_model": "all-MiniLM-L6-v2",
    "device": "cpu",
    "memory_limit_gb": 7.0,
    "checksum_file": "data/checksums.json",
    "taxonomy_file": "data/raw/taxonomy.json",
    "drift_output": "data/processed/drift_scores.csv",
    "validation_output": "data/processed/validation_stats.json",
    "annotation_output": "data/processed/simulated_ground_truth.csv",
}

# Global state for configuration
_current_seed = DEFAULT_CONFIG["seed"]
_current_config = DEFAULT_CONFIG.copy()


def set_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and torch (if available).

    Args:
        seed (int): The seed value to set.
    """
    global _current_seed
    _current_seed = seed
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed, skip torch seeding


def get_path(name: str) -> Path:
    """
    Retrieves the absolute Path for a standard directory or file.

    Args:
        name (str): The key for the path (e.g., 'code', 'data_raw', 'drift_output').

    Returns:
        Path: The resolved absolute path.

    Raises:
        KeyError: If the name is not found in the configuration.
    """
    if name in _DIRS:
        return _DIRS[name]
    if name in _current_config:
        # Handle file paths defined in config
        return _PROJECT_ROOT / _current_config[name]
    raise KeyError(f"Path name '{name}' not found in configuration.")


def get_output_path(name: str, filename: Optional[str] = None) -> Path:
    """
    Retrieves a path for output files, optionally appending a filename.
    If filename is provided, it is appended to the base path.
    If the name is a directory key, it returns the directory.
    If the name is a file key (from DEFAULT_CONFIG), it returns the full file path.

    Args:
        name (str): The configuration key (e.g., 'data_processed' or 'drift_output').
        filename (str, optional): A specific filename to append if the base is a directory.

    Returns:
        Path: The resolved path.
    """
    base_path = get_path(name)
    if filename:
        return base_path / filename
    return base_path


def ensure_directories() -> None:
    """
    Ensures all standard directories defined in the configuration exist.
    Creates them if they do not exist.
    """
    for dir_name, dir_path in _DIRS.items():
        if dir_name == "root":
            continue
        dir_path.mkdir(parents=True, exist_ok=True)


def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration state.

    Returns:
        Dict[str, Any]: A dictionary containing the current seed, batch size,
                        and other active configuration values.
    """
    return {
        "seed": _current_seed,
        "batch_size": _current_config["batch_size"],
        "embedding_model": _current_config["embedding_model"],
        "device": _current_config["device"],
        "memory_limit_gb": _current_config["memory_limit_gb"],
        "project_root": str(_PROJECT_ROOT),
    }


def update_config(key: str, value: Any) -> None:
    """
    Updates a specific configuration value.

    Args:
        key (str): The configuration key to update.
        value (Any): The new value.
    """
    if key in _current_config:
        _current_config[key] = value
    else:
        # Allow adding new keys if necessary, though usually we stick to defaults
        _current_config[key] = value


# Initialize directories on import if desired, or rely on explicit calls
# We do not auto-create here to avoid side effects during import,
# but ensure_directories() is available for the main entry points.