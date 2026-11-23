"""
Test to verify the project directory structure exists.
"""
import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """Verify that code/, data/, and tests/ directories exist at the root."""
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data",
        "tests"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

def test_subdirectories_exist():
    """Verify that specific subdirectories exist."""
    project_root = Path(__file__).resolve().parent.parent
    
    required_subdirs = [
        "code/data", "code/analysis", "code/viz", "code/utils",
        "data/raw", "data/processed",
        "tests/unit", "tests/integration"
    ]
    
    for dir_name in required_subdirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Subdirectory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

def test_init_files_exist():
    """Verify that __init__.py files exist in all package directories."""
    project_root = Path(__file__).resolve().parent.parent
    
    package_dirs = [
        "code", "code/data", "code/analysis", "code/viz", "code/utils",
        "data", "data/raw", "data/processed",
        "tests", "tests/unit", "tests/integration"
    ]
    
    for dir_name in package_dirs:
        dir_path = project_root / dir_name
        init_file = dir_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {dir_path}."