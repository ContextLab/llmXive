"""
Configuration Module for the Impact of Incidental Music on Autobiographical Memory Retrieval project.

This module provides project paths, configuration parameters, and utility functions
for managing the project structure.

Functions:
  get_project_root: Returns the project root directory.
  ensure_directories: Creates necessary project directories.
  get_config_dict: Returns a dictionary of configuration parameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project root directory
_PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration parameters
DEFAULT_CONFIG = {
    'levenshtein_threshold': 4,
    'min_listen_threshold': 10,
    'random_seed': 42,
    'match_rate_threshold': 0.80,
    'birth_year_fallback_threshold': 0.50,
    'early_adolescence_start_offset': 10,
    'early_adolescence_end_offset': 14,
    'late_adolescence_start_offset': 15,
    'late_adolescence_end_offset': 19,
}

def get_project_root() -> Path:
    """
    Returns the project root directory.

    Returns:
        Path to the project root.
    """
    return _PROJECT_ROOT

def ensure_directories() -> None:
    """
    Creates necessary project directories if they don't exist.

    Creates:
      - data/raw/
      - data/processed/
      - data/final/
      - data/final/plots/
      - tests/
    """
    root = get_project_root()
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "final",
        root / "data" / "final" / "plots",
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """
    Returns a dictionary of configuration parameters.

    Returns:
        Dictionary of configuration parameters.
    """
    return DEFAULT_CONFIG.copy()
