"""
Path management utilities for the project.
"""
import os
from code.config import get_config

def get_project_root() -> str:
    """
    Returns the absolute path to the project root.
    
    Returns:
        str: Absolute path to the project root.
    """
    return get_config()['project_root']

def get_raw_path() -> str:
    """
    Returns the path to the raw data directory.
    
    Returns:
        str: Absolute path to the raw data directory.
    """
    root = get_project_root()
    return os.path.join(root, get_config()['data_raw'])

def get_processed_path() -> str:
    """
    Returns the path to the processed data directory.
    
    Returns:
        str: Absolute path to the processed data directory.
    """
    root = get_project_root()
    return os.path.join(root, get_config()['data_processed'])

def get_results_path() -> str:
    """
    Returns the path to the results directory.
    
    Returns:
        str: Absolute path to the results directory.
    """
    root = get_project_root()
    return os.path.join(root, get_config()['data_results'])

def ensure_dir(dir_path: str) -> None:
    """
    Ensures that the specified directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory.
    """
    os.makedirs(dir_path, exist_ok=True)
