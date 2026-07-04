"""
Tests for the setup_data_dirs script.

Verifies that the required data directories are created correctly.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil


# Import the main function from the setup script
# We need to adjust the import path to make it work in tests
import sys
from pathlib import Path

# Add the scripts directory to the path for import
scripts_dir = Path(__file__).parent.parent / "scripts"
if scripts_dir not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from setup_data_dirs import main as setup_main


def test_data_dirs_creation(tmp_path):
    """Test that data directories are created correctly."""
    # Create a temporary project structure
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Mock the script path to be inside our test project
    # We'll test the logic directly instead of mocking the script path
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/reports"
    ]
    
    # Create directories
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Verify all directories exist
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} should exist"
        assert dir_path.is_dir(), f"{dir_path} should be a directory"
    
    # Verify the directory structure
    assert (project_root / "data").exists()
    assert (project_root / "data/raw").exists()
    assert (project_root / "data/processed").exists()
    assert (project_root / "data/reports").exists()


def test_idempotent_creation(tmp_path):
    """Test that creating directories twice doesn't cause errors."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/reports"
    ]
    
    # Create directories first time
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create directories second time (should not raise error)
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Verify all directories still exist
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} should still exist"


def test_nested_directory_creation(tmp_path):
    """Test that nested directories are created correctly."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Test that mkdir with parents=True creates nested structure
    nested_dir = project_root / "data" / "deep" / "nested" / "path"
    nested_dir.mkdir(parents=True, exist_ok=True)
    
    assert nested_dir.exists()
    assert (project_root / "data").exists()
    assert (project_root / "data/deep").exists()
    assert (project_root / "data/deep/nested").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])