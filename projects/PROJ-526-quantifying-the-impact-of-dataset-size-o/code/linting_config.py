"""
Configuration helpers for linting tools.
Exposes functions to retrieve configuration dictionaries 
that match the static config files (.flake8, pyproject.toml).
"""
from pathlib import Path
from typing import Dict, Any, List


def get_black_config() -> Dict[str, Any]:
    """
    Returns the Black configuration as a dictionary.
    Matches the settings in pyproject.toml.
    """
    return {
        "line_length": 88,
        "target_version": ["py310"],
        "include": r"\.pyi?$",
        "exclude": r"/(\.git|\.hg|\.mypy_cache|\.tox|\.venv|_build|buck-out|build|dist)/",
        "skip_string_normalization": False
    }


def get_flake8_config() -> Dict[str, Any]:
    """
    Returns the Flake8 configuration as a dictionary.
    Matches the settings in .flake8.
    """
    return {
        "max_line_length": 88,
        "extend_ignore": ["E203", "W503"],
        "exclude": [".git", "__pycache__", "build", "dist", ".eggs"],
        "max_complexity": 15,
        "import_order_style": "pep8",
        "application_import_names": ["code", "tests"]
    }
