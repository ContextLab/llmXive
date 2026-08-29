import os
import pytest
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_directories import setup_directories

def test_setup_directories_creates_structure(tmp_path):
    """
    Test that setup_directories creates all required directories.
    """
    # Change to tmp_path to simulate a clean environment
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run the setup
        created = setup_directories()
        
        # Verify all expected directories exist
        expected_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/analysis",
            "tests",
            "contracts",
            "state"
        ]
        
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
        
        # Verify the function returns the list of created directories
        assert len(created) == len(expected_dirs), f"Expected {len(expected_dirs)} directories created, got {len(created)}"
        
    finally:
        os.chdir(original_cwd)

def test_setup_directories_idempotent(tmp_path):
    """
    Test that running setup_directories twice does not cause errors.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run twice
        setup_directories()
        setup_directories()
        
        # Verify structure still exists
        expected_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/analysis",
            "tests",
            "contracts",
            "state"
        ]
        
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} missing after second run"
        
    finally:
        os.chdir(original_cwd)