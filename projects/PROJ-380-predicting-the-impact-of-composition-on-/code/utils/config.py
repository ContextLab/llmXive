"""
Configuration module for the BMG Shear Modulus Prediction Pipeline.

This module provides:
- Random seed initialization for reproducibility (NumPy, Python random).
- Path constants for project directories (code, data, tests, docs, state, artifacts).
- Utility functions to ensure directory existence.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Project Root (assumed to be the directory containing 'code/')
# We calculate this dynamically to ensure portability.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default random seed for reproducibility
DEFAULT_SEED = 42

# Path Constants (relative to PROJECT_ROOT)
PATHS = {
    "root": _PROJECT_ROOT,
    "code": _PROJECT_ROOT / "code",
    "data": _PROJECT_ROOT / "data",
    "data_raw": _PROJECT_ROOT / "data" / "raw",
    "data_processed": _PROJECT_ROOT / "data" / "processed",
    "data_artifacts": _PROJECT_ROOT / "data" / "artifacts",
    "tests": _PROJECT_ROOT / "tests",
    "docs": _PROJECT_ROOT / "docs",
    "state": _PROJECT_ROOT / "state",
    "state_projects": _PROJECT_ROOT / "state" / "projects",
    "figures": _PROJECT_ROOT / "figures",
    "contracts": _PROJECT_ROOT / "contracts",
}

def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets the random seed for reproducibility across Python's random, NumPy,
    and optionally PyTorch/TensorFlow if available (though not used in this CPU-only project).

    Args:
        seed (int): The seed value to set. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Optional: PyTorch/TensorFlow if added later
    # try:
    #     import torch
    #     torch.manual_seed(seed)
    # except ImportError:
    #     pass
    # try:
    #     import tensorflow as tf
    #     tf.random.set_seed(seed)
    # except ImportError:
    #     pass

def get_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of all project path constants.

    Returns:
        Dict[str, Path]: A mapping of path names to Path objects.
    """
    return PATHS.copy()

def ensure_directories(paths_to_create: Optional[list] = None) -> None:
    """
    Ensures that the specified directories exist. If no list is provided,
    creates all standard project directories defined in PATHS.

    Args:
        paths_to_create (list, optional): List of path keys (e.g., ["data", "data_raw"]) to create.
    """
    if paths_to_create is None:
        # Create all standard directories
        keys_to_create = [
            "code", "data", "data_raw", "data_processed", "data_artifacts",
            "tests", "docs", "state", "state_projects", "figures", "contracts"
        ]
    else:
        keys_to_create = paths_to_create

    for key in keys_to_create:
        if key in PATHS:
            dir_path = PATHS[key]
            dir_path.mkdir(parents=True, exist_ok=True)
            # Logging could be added here if logging_config is initialized
            # print(f"Ensured directory: {dir_path}")

def main() -> None:
    """
    Main entry point for the config module.
    Demonstrates seed setting and directory creation.
    """
    print("Initializing Configuration...")
    
    # Set random seed
    set_random_seed(DEFAULT_SEED)
    print(f"Random seed set to {DEFAULT_SEED}")
    
    # Ensure all directories exist
    ensure_directories()
    print("All project directories ensured.")
    
    # Print paths for verification
    paths = get_paths()
    print("Project Paths:")
    for key, path in paths.items():
        print(f"  {key}: {path}")

if __name__ == "__main__":
    main()