import os
import shutil
from pathlib import Path
import pytest
from code.setup_directories import create_directories

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to act as the project root."""
    return tmp_path

def test_create_directories_structure(temp_project_root):
    """
    Test that create_directories creates the required folder structure:
    code/, tests/, data/raw/, data/processed/, state/
    """
    # Change to the temp directory to simulate running in project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run the function
        create_directories()
        
        # Verify directories exist
        required_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/processed",
            "state"
        ]
        
        for dir_name in required_dirs:
            dir_path = temp_project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created."
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory."
        
        # Verify nested structure (data/raw and data/processed)
        assert (temp_project_root / "data").exists()
        assert (temp_project_root / "data/raw").exists()
        assert (temp_project_root / "data/processed").exists()
        
    finally:
        os.chdir(original_cwd)

def test_create_directories_idempotent(temp_project_root):
    """
    Test that running create_directories multiple times does not cause errors.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run twice
        create_directories()
        create_directories()
        
        # Verify all still exist
        required_dirs = ["code", "tests", "data/raw", "data/processed", "state"]
        for dir_name in required_dirs:
            assert (temp_project_root / dir_name).exists()
            
    finally:
        os.chdir(original_cwd)
