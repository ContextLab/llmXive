"""
Configuration Module for PROJ-200.

This module defines project paths, thresholds, and configuration dictionaries.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def get_project_root() -> Path:
    """
    Returns the root path of the project.

    Returns:
        Path: The project root directory.
    """
    # Assuming the script is run from the project root or code/
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent

def ensure_directories():
    """
    Ensures that all required directories (data/raw, data/processed, etc.) exist.
    """
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "final",
        root / "data" / "final" / "plots",
        root / "tests",
        root / "contracts"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """
    Returns the configuration dictionary with thresholds and parameters.

    Returns:
        Dict[str, Any]: Configuration parameters.
    """
    return {
        "levenshtein_threshold": 4,
        "min_listen_threshold": 10,
        "birth_year_fallback_threshold": 0.50,
        "match_rate_warning_threshold": 0.80,
        "random_seed": 42,
        "adolescent_start_offset": 10,
        "adolescent_end_offset": 18
    }