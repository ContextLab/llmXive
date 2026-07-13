import os
import pytest
import sys
import tempfile
import shutil

# Add the code directory to the path to import setup_dirs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from setup_dirs import main

def test_directory_creation(tmp_path):
    """
    Test that setup_dirs.main creates the required directory structure.
    We run this in a temporary directory to avoid polluting the actual project root
    during unit testing, but we mock the CWD to point to tmp_path.
    """
    # The task requires specific directories relative to the project root.
    # We will simulate this by changing the current working directory to tmp_path
    # and verifying the directories are created there.
    
    original_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        
        # Run the main function
        exit_code = main()
        
        assert exit_code == 0, "main() should return 0 on success"
        
        # Define expected directories relative to tmp_path
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "code",
            "tests/unit",
            "tests/integration",
            "config"
        ]
        
        for dir_name in expected_dirs:
            full_path = os.path.join(str(tmp_path), dir_name)
            assert os.path.isdir(full_path), f"Expected directory {full_path} was not created."
            
    finally:
        os.chdir(original_cwd)

def test_directory_idempotency(tmp_path):
    """
    Test that running the script twice does not cause errors (idempotency).
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        
        # Run twice
        exit_code_1 = main()
        exit_code_2 = main()
        
        assert exit_code_1 == 0
        assert exit_code_2 == 0
        
        # Verify directories still exist
        expected_dirs = [
            "data/raw",
            "code",
            "config"
        ]
        
        for dir_name in expected_dirs:
            full_path = os.path.join(str(tmp_path), dir_name)
            assert os.path.isdir(full_path)
            
    finally:
        os.chdir(original_cwd)