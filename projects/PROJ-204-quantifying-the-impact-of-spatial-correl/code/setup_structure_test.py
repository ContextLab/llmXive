"""
Test for project structure creation.
"""
import os
import pytest
from pathlib import Path
from setup_structure import create_project_structure

def test_create_project_structure_creates_directories():
    """Verify that the required directories are created."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state",
        "docs",
        "logs"
    ]
    
    # Run the setup
    create_project_structure()
    
    # Verify each directory exists
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} exists but is not a directory"

def test_create_project_structure_creates_submodules():
    """Verify that code submodules are created."""
    required_subdirs = [
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report"
    ]
    
    create_project_structure()
    
    for dir_path in required_subdirs:
        full_path = Path(dir_path)
        assert full_path.exists(), f"Subdirectory {full_path} was not created"