"""
Unit tests for directory setup and configuration.
"""
import os
import pytest
from pathlib import Path
from config import ensure_directories, REQUIRED_DIRS, PROJECT_ROOT

def test_directories_exist():
    """Test that ensure_directories creates the required folders."""
    # Run the setup
    ensure_directories()
    
    # Verify each directory exists
    for dir_name in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_init_files_created():
    """Test that __init__.py files are created in Python packages."""
    ensure_directories()
    
    # List of directories that should have __init__.py
    init_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    for dir_name in init_dirs:
        dir_path = PROJECT_ROOT / dir_name
        init_file = dir_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {dir_path}"
