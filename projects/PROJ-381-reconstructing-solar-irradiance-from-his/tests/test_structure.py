"""
Test to verify that the project directory structure has been created correctly.
"""
import os
from pathlib import Path
import pytest

def test_project_directories_exist():
    """Verify that all required project directories exist."""
    base_path = Path(__file__).parent.parent
    
    required_dirs = [
        "code",
        "code/models",
        "code/analysis",
        "code/data",
        "tests",
        "data/raw",
        "data/processed",
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist."
        assert full_path.is_dir(), f"{dir_path} is not a directory."

def test_init_files_exist():
    """Verify that __init__.py files exist in all required directories."""
    base_path = Path(__file__).parent.parent
    
    init_files = [
        "code/__init__.py",
        "code/models/__init__.py",
        "code/analysis/__init__.py",
        "code/data/__init__.py",
        "tests/__init__.py",
    ]
    
    for file_path in init_files:
        full_path = base_path / file_path
        assert full_path.exists(), f"File {file_path} does not exist."
        assert full_path.is_file(), f"{file_path} is not a file."

def test_gitkeep_files_exist():
    """Verify that .gitkeep files exist in data directories."""
    base_path = Path(__file__).parent.parent
    
    gitkeep_files = [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
    ]
    
    for file_path in gitkeep_files:
        full_path = base_path / file_path
        assert full_path.exists(), f"File {file_path} does not exist."
        assert full_path.is_file(), f"{file_path} is not a file."
