"""
Configuration management for the llmXive project.

This module provides utilities for managing dataset paths, model IDs,
and other configuration settings.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration
DEFAULT_CONFIG = {
    "dataset": {
        "swe_bench_lite": "princeton-nlp/SWE-bench_Lite",
        "swe_bench_full": "princeton-nlp/SWE-bench",
    },
    "model": {
        "fastcontext_lite": "fastcontext-lite-v1",
        "fastcontext_4b": "princeton-nlp/fastcontextb",
    },
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_results": "data/results",
        "code": "code",
        "tests": "tests",
        "specs": "specs",
        "state": "state",
    }
}


def get_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path within the project root.

    Args:
        relative_path: Relative path string (e.g., "data/raw/file.csv").

    Returns:
        Absolute Path object.
    """
    return PROJECT_ROOT / relative_path


def ensure_directories(paths: list) -> None:
    """
    Ensures that the given paths (files or directories) exist.
    If a path is a file, ensures its parent directory exists.

    Args:
        paths: List of Path objects or strings.
    """
    for path in paths:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        if not path_obj.exists() and not str(path_obj).endswith("/"):
            # Create the file as an empty file if it doesn't exist
            path_obj.touch()


def get_config_dict() -> Dict[str, Any]:
    """
    Returns the default configuration dictionary.

    Returns:
        Configuration dictionary.
    """
    return DEFAULT_CONFIG.copy()
