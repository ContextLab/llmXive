import os
import pytest
from pathlib import Path
from code.setup_directories import create_directory_structure

def test_creates_required_directories(tmp_path):
    """
    Verify that create_directory_structure creates all required folders.
    """
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "scripts",
    ]
    
    create_directory_structure(tmp_path)
    
    for dir_name in required_dirs:
        full_path = tmp_path / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_ignores_existing_directories(tmp_path):
    """
    Verify that the function does not crash if directories already exist.
    """
    # Pre-create a directory
    (tmp_path / "code").mkdir()
    
    # Run the setup again
    create_directory_structure(tmp_path)
    
    # Verify it still exists
    assert (tmp_path / "code").exists()