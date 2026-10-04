import os
import random
from pathlib import Path
from typing import Dict, Any

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the project root is the current working directory or two levels up from code/utils.
    We prioritize the current working directory as it is where the runner executes scripts.
    """
    # If running as a script from code/setup_project_structure.py, cwd is likely the root.
    # If running as a module, we might need to traverse up.
    cwd = Path.cwd()
    
    # Heuristic: if 'code' directory exists in cwd, assume cwd is root.
    if (cwd / 'code').is_dir() and (cwd / 'data').is_dir():
        return cwd
    
    # Fallback: traverse up from the module location
    module_path = Path(__file__).resolve()
    # Expected structure: project_root/code/utils/config.py
    potential_root = module_path.parent.parent.parent
    
    if (potential_root / 'code').is_dir():
        return potential_root
    
    # Last resort: cwd
    return cwd

def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility.
    """
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration.
    """
    return {
        "project_root": str(get_project_root()),
        "data_path": str(get_data_path()),
        "state_path": str(get_state_path()),
        "figures_path": str(get_figures_path()),
        "logs_path": str(get_logs_path())
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
