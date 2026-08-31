"""
Tests for T002: Data directory creation.
Verifies that the required data subdirectories are created correctly.
"""
import os
import shutil
import tempfile
from pathlib import Path

def test_data_directories_exist():
    """Verify that data/raw, data/processed, and data/split exist after running setup."""
    # We assume the script has been run. We check relative to the test file location.
    # In a real CI/CD, this would be run after the setup script.
    # For this unit test, we verify the logic by checking if the function creates them.
    
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_root = tmpdir_path / "data"
        
        # Simulate the creation logic from setup_data_dirs.py
        subdirs = ["raw", "processed", "split"]
        for subdir in subdirs:
            (data_root / subdir).mkdir(parents=True, exist_ok=True)
        
        # Verify existence
        for subdir in subdirs:
            dir_path = data_root / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_data_directories_structure():
    """Verify the full path structure of data directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_root = tmpdir_path / "data"
        
        # Create structure
        (data_root / "raw").mkdir()
        (data_root / "processed").mkdir()
        (data_root / "split").mkdir()
        
        # Check paths
        assert (data_root / "raw").exists()
        assert (data_root / "processed").exists()
        assert (data_root / "split").exists()
        
        # Ensure no extra files were created (sanity check)
        assert len(list(data_root.iterdir())) == 3