"""
Configuration and Path Management for the Material Strength Prediction Project.
Includes seed management for reproducibility.
"""
import os
import random
from pathlib import Path
from typing import Optional

import numpy as np

# Try to import torch, but handle gracefully if not installed yet
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the code is run from the project root or one of its subdirectories.
    """
    # If run from code/data/, we need to go up two levels
    # If run from root, we stay.
    current = Path(__file__).resolve()
    # Navigate up to find the directory containing 'code', 'data', 'tests'
    # Assuming structure: PROJ/code/utils/config.py
    root = current.parent.parent.parent
    
    # Basic validation
    if not (root / "code").exists() or not (root / "data").exists():
        # Fallback: try to find it by walking up
        for parent in [root] + list(root.parents):
            if (parent / "code").exists() and (parent / "data").exists():
                return parent
        raise FileNotFoundError("Could not determine project root. Expected 'code' and 'data' directories.")
    
    return root

def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_raw_dir() -> Path:
    """Returns the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_results_dir() -> Path:
    """Returns the path to the results directory."""
    return get_project_root() / "results"

def get_code_dir() -> Path:
    """Returns the path to the code directory."""
    return get_project_root() / "code"

def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across libraries.
    
    Args:
        seed: The integer seed value to use. Defaults to 42.
    """
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed
    np.random.seed(seed)
    
    # Set PyTorch's random seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # If using multi-GPU
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Set environment variable for deterministic behavior in some ops
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> int:
    """
    Returns the default seed value used in the project.
    
    Returns:
        The default seed integer (42).
    """
    return 42