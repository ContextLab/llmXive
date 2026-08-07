import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project_structure import get_project_root, create_directory_structure

def test_get_project_root():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_create_directory_structure_creates_dirs():
    """Test that create_directory_structure creates all required directories."""
    # Create a temporary directory to simulate a project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Mock the project root by creating the expected subdirectories
        # We'll test the function by passing our temp path
        required_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/processed",
            "data/figures",
            "specs/001-molecular-flexibility-permeability"
        ]
        
        # Verify directories don't exist initially
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert not dir_path.exists(), f"Directory {dir_path} should not exist initially"
        
        # Create the structure
        created = create_directory_structure(tmp_path)
        
        # Verify all directories were created
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist after creation"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"
        
        # Verify the returned list contains the created directories
        assert len(created) == len(required_dirs)
        for created_dir in created:
            assert created_dir.exists()

def test_create_directory_structure_skips_existing():
    """Test that create_directory_structure does not fail if directories already exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Pre-create some directories
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        # This should not raise an exception
        created = create_directory_structure(tmp_path)
        
        # Only the missing directories should be in the created list
        # In this case, 'tests', 'data/processed', 'data/figures', 'specs/...'
        assert len(created) > 0
        
        # Verify all required directories exist
        assert (tmp_path / "code").exists()
        assert (tmp_path / "tests").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "figures").exists()
        assert (tmp_path / "specs" / "001-molecular-flexibility-permeability").exists()