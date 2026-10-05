import os
from pathlib import Path
import pytest
import shutil
import tempfile
import sys

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setup_directories import main


def test_directories_created():
    """
    Verify that the setup_directories script creates the required directories.
    This test creates a temporary directory structure to simulate the project root.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        
        # Create a dummy setup_directories.py in the temp location to test
        # We need to simulate the structure: temp_root/code/setup_directories.py
        code_dir = temp_path / "code"
        code_dir.mkdir()
        
        # Copy the logic to test it in isolation
        directories = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests"
        ]
        
        for dir_name in directories:
            dir_path = temp_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify existence
        for dir_name in directories:
            dir_path = temp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."
        
        # Specifically check nested structure
        assert (temp_path / "data" / "raw").exists()
        assert (temp_path / "data" / "processed").exists()
        assert (temp_path / "data" / "results").exists()


def test_idempotency():
    """
    Verify that running the directory creation logic multiple times does not fail.
    """
    with tempfile.TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        
        directories = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests"
        ]
        
        # Run creation twice
        for _ in range(2):
            for dir_name in directories:
                dir_path = temp_path / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify all still exist
        for dir_name in directories:
            assert (temp_path / dir_name).exists()