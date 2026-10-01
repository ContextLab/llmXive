import os
import random
from pathlib import Path
from typing import Dict, Any

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    # Try to find the root by looking for a specific marker or just using cwd
    # For this pipeline, we assume the working directory is the project root
    return Path.cwd()

def set_seed(seed: int = 42):
    """
    Set random seeds for reproducibility.
    """
    random.seed(seed)
    # If numpy is available, set its seed too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration.
    """
    return {
        "project_root": str(get_project_root()),
        "seed": 42
    }

def get_data_path() -> Path:
    """
    Get the path to the data directory.
    """
    return get_project_root() / 'data'

def get_state_path() -> Path:
    """
    Get the path to the state directory.
    """
    return get_project_root() / 'state'

def get_figures_path() -> Path:
    """
    Get the path to the figures directory.
    """
    return get_project_root() / 'figures'

def get_logs_path() -> Path:
    """
    Get the path to the logs directory.
    """
    return get_project_root() / 'logs'