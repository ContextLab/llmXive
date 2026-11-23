import os
import pytest
from pathlib import Path
from code.setup_directories import main

def test_directories_created(tmp_path):
    """
    Test that the setup_directories script creates the required directories.
    
    We change to a temporary directory to avoid polluting the actual repo
    during testing, then verify the directories are created.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    
    try:
        # Run the main function which creates directories
        result = main()
        
        # Verify return code
        assert result == 0, "main() should return 0 on success"
        
        # Define expected directories
        expected_dirs = [
            "data/raw",
            "data/derived",
            "results",
            "contracts",
            "code",
            "tests"
        ]
        
        # Verify each directory exists
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_directories_idempotent(tmp_path):
    """
    Test that running setup_directories multiple times doesn't cause errors.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    
    try:
        # Run twice
        result1 = main()
        result2 = main()
        
        assert result1 == 0
        assert result2 == 0
        
        # Verify directories still exist
        expected_dirs = ["data/raw", "data/derived", "results", "contracts"]
        for dir_name in expected_dirs:
            assert (tmp_path / dir_name).exists()
    finally:
        os.chdir(original_cwd)
