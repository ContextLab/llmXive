"""
Configuration helpers for linting and formatting tools.
Provides programmatic access to black and flake8 settings used by the runner.
"""
from pathlib import Path
from typing import Dict, Any, List

def get_black_config() -> Dict[str, Any]:
    """
    Returns the effective Black configuration used by the project.
    Matches settings in pyproject.toml.
    """
    return {
        "line_length": 120,
        "target_version": ["py310"],
        "exclude": [
            ".git",
            "__pycache__",
            "data",
            "build",
            "dist",
            ".eggs",
        ],
    }

def get_flake8_config() -> Dict[str, Any]:
    """
    Returns the effective Flake8 configuration used by the project.
    Matches settings in .flake8.
    """
    return {
        "max_line_length": 120,
        "exclude": [
            ".git",
            "__pycache__",
            "data",
            "build",
            "dist",
            ".eggs",
        ],
        "ignore": ["E203", "E266", "W503"],
        "per_file_ignores": {
            "tests/*": ["S101"],
        },
    }
