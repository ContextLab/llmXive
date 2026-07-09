"""
Path management utilities for the project.

This module centralizes path construction for data directories
to ensure consistency across the pipeline.
"""

import os
from code.config import get_config


def get_project_root() -> str:
    """Get the absolute path to the project root."""
    # Assuming the code is run from the project root or a subdirectory
    # We traverse up to find the root where 'data/' and 'code/' exist
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, 'data')) and os.path.exists(os.path.join(current, 'code')):
            return current
        current = os.path.dirname(current)
    # Fallback: assume current working directory is root
    return os.getcwd()


def get_raw_path() -> str:
    """Get the path to the raw data directory."""
    return os.path.join(get_project_root(), 'data', 'raw')


def get_processed_path() -> str:
    """Get the path to the processed data directory."""
    return os.path.join(get_project_root(), 'data', 'processed')


def get_results_path() -> str:
    """Get the path to the results directory."""
    return os.path.join(get_project_root(), 'data', 'results')


def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)
