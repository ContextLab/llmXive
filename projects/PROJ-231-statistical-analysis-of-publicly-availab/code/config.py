import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    # Assume project root is 4 levels up from code directory
    return Path(__file__).resolve().parent.parent

def get_data_dir() -> Path:
    """
    Get the data directory.
    
    Returns:
        Path to data directory
    """
    return get_project_root() / "data"

def get_artifacts_dir() -> Path:
    """
    Get the artifacts directory.
    
    Returns:
        Path to artifacts directory
    """
    return get_project_root() / "artifacts"

def get_log_dir() -> Path:
    """
    Get the log directory.
    
    Returns:
        Path to log directory
    """
    return get_project_root() / "logs"
