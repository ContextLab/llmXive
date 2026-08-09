"""
Configuration utilities for the project.
Handles project root detection and directory path resolution.
"""
import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    The project root is determined by looking for the .git directory
    or by traversing up from the current file's location.
    
    Returns:
        Path: The project root directory
    """
    # Start from the current file's directory
    current_file = Path(__file__).resolve()
    current_dir = current_file.parent.parent.parent  # Go up to project root
    
    # Traverse up until we find a .git directory or reach filesystem root
    while current_dir != current_dir.parent:
        if (current_dir / ".git").exists():
            return current_dir
        current_dir = current_dir.parent
    
    # Fallback: return the directory where the script is located
    return Path(__file__).resolve().parent.parent.parent

def get_data_dir() -> Path:
    """
    Get the data directory path.
    
    Returns:
        Path: Path to the data directory
    """
    return get_project_root() / "data"

def get_results_dir() -> Path:
    """
    Get the results directory path.
    
    Returns:
        Path: Path to the results directory
    """
    return get_project_root() / "results"

def load_env_config() -> dict:
    """
    Load configuration from environment variables.
    
    Returns:
        dict: Dictionary of environment configuration values
    """
    config = {}
    # Example environment variables that might be used
    env_vars = [
        "TIME_BUDGET",
        "MAX_RAM_GB",
        "SENSITIVITY_THRESHOLDS",
        "DATA_SOURCE_OVERRIDE"
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value is not None:
            config[var] = value
    
    return config
