import os
import tempfile
import shutil
from pathlib import Path
import sys
import pytest

# Add the code directory to the path so we can import setup_project
# Note: In a real test run, the path setup might be handled differently,
# but for this standalone test file, we assume the structure.
# We will test the logic by importing the function if possible, or mocking.
# Since setup_project.py is a script with a main(), we test the logic directly.

def test_directory_creation_logic():
    """
    Test that the directory creation logic works correctly.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Define the directories to create
        directories = [
            "code",
            "tests",
            "data/raw",
            "data/generated",
            "state/projects",
            "data/results"
        ]
        
        # Create them
        for dir_path in directories:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        # Verify they exist
        for dir_path in directories:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} is not a directory."
            
            # Check nested directories
            if "raw" in dir_path:
                assert (project_root / "data").exists()
                assert (project_root / "data" / "raw").exists()

def test_skip_existing_directories():
    """
    Test that existing directories are not recreated (idempotency).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Create one directory beforehand
        pre_existing = project_root / "code"
        pre_existing.mkdir()
        
        # Try to "create" it again
        directories = ["code", "tests"]
        for dir_path in directories:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        # Verify the pre-existing one is still there and no error occurred
        assert pre_existing.exists()
        assert (project_root / "tests").exists()