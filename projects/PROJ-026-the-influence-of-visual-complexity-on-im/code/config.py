"""
Configuration management for the project.

Provides functions to manage paths, random seeds, and constants.
"""
import os
from pathlib import Path
from typing import Final

# Project root directory
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent

# Default random seed
DEFAULT_SEED: Final[int] = 42

def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root directory.
    """
    return PROJECT_ROOT

def ensure_directories():
    """
    Ensure all required directories exist.

    Creates the following directories if they don't exist:
    - data/raw/stimuli
    - data/raw/responses
    - data/processed
    - data/results
    - logs
    - figures
    """
    directories = [
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        "logs",
        "figures"
    ]

    for dir_path in directories:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

def get_data_path() -> Path:
    """
    Get the data directory path.

    Returns:
        Path to the data directory.
    """
    return PROJECT_ROOT / "data"
