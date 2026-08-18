import os
import pytest
from pathlib import Path
from code.setup_project import create_directories

def test_directory_creation(tmp_path):
    """
    Test that create_directories creates the required folder structure.
    We run the function in a temporary directory to verify side effects.
    """
    # Change to tmp_path for the test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run the creation logic
        result = create_directories()
        
        assert result is True, "create_directories should return True on success"
        
        # Verify directories exist
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "figures",
            "analysis",
            "contracts"
        ]
        
        for dir_name in required_dirs:
            target_path = tmp_path / dir_name
            assert target_path.exists(), f"Directory {dir_name} was not created"
            assert target_path.is_dir(), f"{dir_name} exists but is not a directory"
    finally:
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """
    Test that running create_directories twice does not raise errors
    and results in the same structure.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # First run
        create_directories()
        
        # Second run
        result = create_directories()
        assert result is True
        
        # Verify structure is intact
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "analysis").exists()
    finally:
        os.chdir(original_cwd)
