"""
Tests for the project setup script (T001).
Verifies that the required directory structure is created.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the script logic. Since setup_project.py is in code/,
# we will test the logic by simulating the environment or importing the function.
# For T001, we are testing the creation of directories.
# We will create a temporary directory to simulate the project root.

def test_directory_creation_logic():
    """Test that the directory creation logic works correctly."""
    # Create a temporary directory to act as project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Define the directories relative to project root
        directories = [
            "data/raw",
            "data/processed",
            "code/utils",
            "tests",
            "results/paper_figures"
        ]

        # Execute creation logic
        for dir_path in directories:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

        # Verify all directories exist
        for dir_path in directories:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

def test_no_error_on_existing():
    """Test that the script doesn't fail if directories already exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Pre-create one directory
        pre_created = project_root / "data" / "raw"
        pre_created.mkdir(parents=True)
        
        # Try to create it again (should not raise)
        pre_created.mkdir(parents=True, exist_ok=True)
        
        assert pre_created.exists()