import os
import pytest
import shutil
import tempfile
from code.setup_directories import create_project_structure

def test_create_project_structure_creates_dirs():
    """
    Test that create_project_structure creates all required directories.
    Runs in a temporary directory to avoid polluting the actual project root.
    """
    # Create a temporary directory and change to it
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    try:
        os.chdir(temp_dir)
        
        # Run the function
        result = create_project_structure()
        
        # Verify all required directories exist
        required_dirs = [
            "data/raw",
            "data/results",
            "code",
            "tests/unit",
            "tests/contract",
            "contracts"
        ]
        
        for dir_path in required_dirs:
            full_path = os.path.join(temp_dir, dir_path)
            assert os.path.isdir(full_path), f"Directory {dir_path} was not created"
        
        # Verify return count
        assert result == len(required_dirs), f"Expected to create {len(required_dirs)} dirs, got {result}"
        
    finally:
        # Cleanup: remove temp dir and restore cwd
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_create_project_structure_idempotent():
    """
    Test that running create_project_structure twice doesn't fail or create duplicates.
    """
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    try:
        os.chdir(temp_dir)
        
        # Run twice
        create_project_structure()
        result_second = create_project_structure()
        
        # Second run should create 0 new directories
        assert result_second == 0, "Second run should create 0 new directories"
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
