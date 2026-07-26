"""
Tests for the directory setup functionality.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to add the code directory to the path temporarily or assume standard imports
import sys
sys.path.insert(0, 'projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code')

from setup_directories import ensure_data_directories

def test_ensure_data_directories_creates_structure():
    """Test that ensure_data_directories creates the expected directory structure."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        data_dir = project_root / "data"
        
        # Call the function
        ensure_data_directories(str(project_root))
        
        # Assert the main data directory exists
        assert data_dir.exists(), "Main data directory should exist"
        assert data_dir.is_dir(), "Main data directory should be a directory"
        
        # Assert subdirectories exist
        expected_subdirs = ["raw", "processed", "results", "figures"]
        for subdir in expected_subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir} should exist"
            assert subdir_path.is_dir(), f"Subdirectory {subdir} should be a directory"

def test_ensure_data_directories_idempotent():
    """Test that running the function multiple times does not cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Run once
        ensure_data_directories(str(project_root))
        
        # Run again
        try:
            ensure_data_directories(str(project_root))
        except Exception as e:
            pytest.fail(f"Function should be idempotent but raised: {e}")
        
        # Verify structure still intact
        data_dir = project_root / "data"
        assert data_dir.exists()
        for subdir in ["raw", "processed", "results", "figures"]:
            assert (data_dir / subdir).exists()
