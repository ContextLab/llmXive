import os
import random
from pathlib import Path
from typing import Dict, Any

def get_project_root() -> Path:
    """
    Get the root directory of the project.
    Assumes the script is run from the repository root or code/ directory.
    """
    # Try to find the project root by looking for a marker file or specific structure
    # Common approach: look for the 'data' directory or 'specs' directory
    current = Path(__file__).resolve()
    
    # Search up the tree for the project root
    # We expect to find 'data' and 'specs' directories at the root
    for parent in [current] + list(current.parents):
        if (parent / "data").exists() and (parent / "specs").exists():
            return parent
        
        # Fallback: if we are in the 'code' directory, parent is root
        if parent.name == "code" and (parent.parent / "data").exists():
            return parent.parent

    # If all else fails, assume current working directory or the parent of the script
    return Path.cwd()

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration.
    """
    return {
        "project_root": str(get_project_root()),
        "data_path": str(get_data_path()),
        "state_path": str(get_state_path()),
        "figures_path": str(get_figures_path()),
        "logs_path": str(get_logs_path()),
    }

def get_data_path() -> Path:
    """Get the path to the data directory."""
    return get_project_root() / "data"

def get_state_path() -> Path:
    """Get the path to the state directory."""
    return get_project_root() / "state"

def get_figures_path() -> Path:
    """Get the path to the figures directory."""
    return get_project_root() / "figures"

def get_logs_path() -> Path:
    """Get the path to the logs directory."""
    return get_project_root() / "logs"
