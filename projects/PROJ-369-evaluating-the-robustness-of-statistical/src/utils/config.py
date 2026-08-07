"""
Configuration module for the llmXive statistical robustness project.
Defines project root, path constants, random seeds, and statistical parameters.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional

# Statistical Parameters
ALPHA: float = 0.05  # Significance level for hypothesis testing
ADF_THRESHOLD: float = 0.05  # P-value threshold for stationarity
MIN_SERIES_LENGTH: int = 25  # Minimum length for valid analysis

# Random Seeds for Reproducibility
DEFAULT_SEED: int = 42

# Project Root (dynamically determined)
_PROJECT_ROOT: Optional[Path] = None

def set_project_root(root_path: str | Path) -> None:
    """
    Explicitly set the project root directory.
    Useful for testing or when running from a non-standard location.
    """
    global _PROJECT_ROOT
    if isinstance(root_path, str):
        _PROJECT_ROOT = Path(root_path).resolve()
    else:
        _PROJECT_ROOT = root_path.resolve()

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Attempts to find 'src' in the hierarchy if not explicitly set.
    """
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # Default fallback: assume current working directory is project root
    # or find the directory containing 'src'
    current = Path.cwd()
    
    # Check if 'src' exists in current dir
    if (current / 'src').exists():
        return current
    
    # Walk up to find a directory containing 'src'
    for parent in current.parents:
        if (parent / 'src').exists():
            return parent
    
    # Fallback to current
    return current

def get_path(name: str) -> Path:
    """
    Get a full path relative to the project root.
    
    Args:
        name: Logical name of the path (e.g., 'data', 'results', 'code')
    
    Returns:
        Absolute Path object
    """
    root = get_project_root()
    
    # Mapping of logical names to relative paths
    path_map: Dict[str, str] = {
        'project_root': '',
        'code': 'code',
        'src': 'src',
        'tests': 'tests',
        'data': 'data',
        'data_raw': 'data/raw',
        'data_processed': 'data/processed',
        'results': 'results',
        'figures': 'results/figures',
        'specs': 'specs',
        'state': 'state',
        'state_projects': 'state/projects',
    }
    
    relative = path_map.get(name, name)
    return root / relative

def ensure_dirs() -> None:
    """
    Ensure all required project directories exist.
    Creates them if they don't exist.
    """
    root = get_project_root()
    
    required_dirs = [
        'src',
        'src/utils',
        'src/data',
        'src/synthesis',
        'src/analysis',
        'src/viz',
        'tests',
        'tests/unit',
        'tests/integration',
        'data',
        'data/raw',
        'data/processed',
        'results',
        'results/figures',
        'specs',
        'state',
        'state/projects',
    ]
    
    for dir_name in required_dirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        seed: Integer seed value (default: 42)
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # If tensorflow is available, set seed there too
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass
    
    # If torch is available, set seed there too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# Initialize directories on module import if running as main
if __name__ == "__main__":
    ensure_dirs()
    print(f"Project root: {get_project_root()}")
    print("Directories ensured.")
    set_seed()
    print(f"Random seed set to {DEFAULT_SEED}")
