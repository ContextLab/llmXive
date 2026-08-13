"""
Configuration utilities for the llmXive project.
Handles seed pinning, path resolution, and environment variable loading.
"""

import os
import sys
from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the project root is the parent of the 'src' directory.
    """
    current_file = Path(__file__).resolve()
    # Navigate up from src/utils/config.py to project root
    return current_file.parent.parent.parent

def get_data_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path under the data directory.
    """
    return get_project_root() / "data" / relative_path

def get_artifacts_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path under the artifacts directory.
    """
    return get_project_root() / "artifacts" / relative_path

def get_results_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path under the data/results directory.
    """
    return get_project_root() / "data" / "results" / relative_path

def ensure_directories():
    """
    Ensures all required directories exist.
    """
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "artifacts",
        root / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42):
    """
    Sets the random seed for reproducibility.
    """
    import random
    import numpy as np
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    random.seed(seed)
    np.random.seed(seed)
