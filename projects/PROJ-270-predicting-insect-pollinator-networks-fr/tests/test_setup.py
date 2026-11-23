"""
Tests for project setup and directory structure.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_directory_structure():
    """Verify that required directories exist (T001a)."""
    required_dirs = [
        "code",
        "code/utils",
        "code/contracts",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "results",
    ]

    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        assert os.path.exists(full_path), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"


def test_init_files_exist():
    """Verify that __init__.py files exist in required packages."""
    required_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "code/utils/__init__.py",
    ]

    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        assert full_path.exists(), f"File {file_path} does not exist"


def test_code_quality():
    """Verify that linting config files exist."""
    config_files = [
        "code/.ruff.toml",
        "code/.black.toml",
        "code/.mypy.ini",
    ]

    for file_path in config_files:
        full_path = PROJECT_ROOT / file_path
        assert full_path.exists(), f"Configuration file {file_path} does not exist"