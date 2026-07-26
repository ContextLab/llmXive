import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
# Assuming the module is in the same directory or added to sys.path
# For testing, we might need to adjust the import path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_project_structure import create_directory_structure, get_project_root

def test_create_directory_structure():
    """Test that the directory structure is created correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Call the function
        created_dirs = create_directory_structure(root)
        
        # Verify that the directories were created
        expected_dirs = [
            "code",
            "tests",
            "data",
            "data/raw",
            "data/processed",
            "state",
            "state/projects",
            "specs",
            "specs/001-molecular-flexibility-permeability",
            "specs/001-molecular-flexibility-permeability/contracts",
            "figures",
        ]
        
        for dir_name in expected_dirs:
            full_path = root / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"
        
        # Verify that the returned list contains the created paths
        for created_dir in created_dirs:
            assert created_dir.exists(), f"Created directory {created_dir} does not exist"
            assert created_dir in [root / d for d in expected_dirs], f"Created directory {created_dir} is not expected"

def test_create_directory_structure_already_exists():
    """Test that the function handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Pre-create some directories
        (root / "code").mkdir()
        (root / "data").mkdir()
        
        # Call the function
        created_dirs = create_directory_structure(root)
        
        # Verify that no new directories were created for the existing ones
        # But the function should still return the list of all expected directories
        # (or only the new ones, depending on implementation)
        # In this implementation, it returns only newly created directories
        assert len(created_dirs) <= len([d for d in ["code", "data"] if not (root / d).exists()]), \
            "Function returned more directories than expected"
        
        # Verify that the existing directories still exist
        assert (root / "code").exists()
        assert (root / "data").exists()

def test_get_project_root():
    """Test that the project root is correctly identified."""
    # This is a simple test; in a real scenario, you might want to test
    # the logic for identifying the project root more thoroughly
    root = get_project_root()
    assert root.exists(), "Project root does not exist"
    assert root.is_dir(), "Project root is not a directory"
