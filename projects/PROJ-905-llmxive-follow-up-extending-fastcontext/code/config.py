"""
Configuration management for the project.

This module provides utility functions for path resolution and directory creation.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Project root is assumed to be the parent of the 'code' directory
# or can be explicitly set via environment variable.
PROJECT_ROOT = Path(__file__).parent.parent


def get_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path within the project root.

    Args:
        relative_path: Path relative to the project root.

    Returns:
        Absolute Path object.
    """
    return PROJECT_ROOT / relative_path


def ensure_directories(file_paths: list) -> None:
    """
    Ensures that the directories containing the given file paths exist.

    Args:
        file_paths: List of Path objects or strings representing file paths.
    """
    for path in file_paths:
        if isinstance(path, str):
            path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)


def get_config_dict() -> Dict[str, Any]:
    """
    Returns a dictionary of configuration values.

    Returns:
        Dictionary containing project configuration.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(get_path("data")),
        "code_dir": str(get_path("code")),
        "tests_dir": str(get_path("tests")),
    }
