"""
Tests for project setup and directory structure.
"""
import pytest
import os
from pathlib import Path

def test_directory_structure():
    """Verify that required directories exist."""
    # These directories should be created by T001a
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "results"
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_init_files_exist():
    """Verify that __init__.py files exist in required packages."""
    required_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "code/utils/__init__.py"
    ]
    
    for file_path in required_files:
        full_path = Path(file_path)
        assert full_path.exists(), f"File {file_path} does not exist"

def test_code_quality():
    """Verify that linting passes (placeholder for ruff/black/mypy checks)."""
    # This test ensures that the configuration files exist
    config_files = [
        "code/.ruff.toml",
        "code/.black.toml",
        "code/.mypy.ini"
    ]
    
    for file_path in config_files:
        full_path = Path(file_path)
        assert full_path.exists(), f"Configuration file {file_path} does not exist"
