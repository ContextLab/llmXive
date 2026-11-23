"""
Tests for the project setup script (T001).

Verifies that the required directory structure exists after running
code/setup_project.py.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import create_directories
from config import get_project_root

def test_directory_structure_creation():
    """
    Test that create_directories creates the expected folder hierarchy.
    """
    # We run the creation logic
    created_dirs = create_directories()
    
    # Define expected directories relative to project root
    expected_dirs = [
        "code/data",
        "code/stimuli",
        "code/analysis",
        "code/viz",
        "code/tests",
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        "logs",
        "docs",
        "figures",
    ]
    
    project_root = get_project_root()
    
    # Assert all expected directories exist
    for dir_name in expected_dirs:
        full_path = project_root / dir_name
        assert full_path.exists(), f"Directory {dir_name} does not exist after setup."
        assert full_path.is_dir(), f"Path {dir_name} exists but is not a directory."

def test_nested_directories_created():
    """
    Test that nested directories (e.g., data/raw/stimuli) are created correctly.
    """
    project_root = get_project_root()
    
    # Check specific nested paths
    nested_paths = [
        "data/raw/stimuli",
        "data/raw/responses",
        "code/data",
        "code/analysis",
    ]
    
    for path_str in nested_paths:
        path = project_root / path_str
        assert path.exists() and path.is_dir(), f"Nested directory {path_str} missing."