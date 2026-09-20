"""
Configuration management for the research pipeline.

Defines project paths, constants, and utility functions for path resolution.
"""
import os
from pathlib import Path
from typing import Final

# Project constants
SEED: Final[int] = 42
DATA_ROOT: Final[str] = "data"
CODE_ROOT: Final[str] = "code"
RESULTS_ROOT: Final[str] = "data/results"

def get_project_root() -> Path:
    """
    Get the absolute path to the project root.
    
    The project root is assumed to be the parent directory of this config file.
    
    Returns:
        Path: Absolute path to the project root.
    """
    return Path(__file__).resolve().parent.parent

def ensure_directories() -> None:
    """
    Ensure all required project directories exist.
    
    This function creates the directory structure if it doesn't already exist.
    """
    from setup_directories import setup_directories
    setup_directories()

def get_data_path(subpath: str = "") -> Path:
    """
    Get the absolute path to a data file or directory.
    
    Args:
        subpath: Relative path within the data directory.
    
    Returns:
        Path: Absolute path to the data location.
    """
    return get_project_root() / DATA_ROOT / subpath