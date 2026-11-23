"""
Unit tests for the directory creation logic (Task T001b).
Verifies that code/, data/, and tests/ directories are created.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add parent directory to path to import the script logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from directories_setup import create_directories

def test_create_directories_creates_folders(tmp_path):
    """
    Test that create_directories creates the required folders.
    We change the CWD to a temp directory to simulate the project root.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Call the function
        created = create_directories()
        
        # Verify directories were returned as created
        assert "code" in created
        assert "data" in created
        assert "tests" in created
        
        # Verify they actually exist on disk
        assert os.path.isdir("code")
        assert os.path.isdir("data")
        assert os.path.isdir("tests")
        
    finally:
        os.chdir(original_cwd)

def test_create_directories_skips_existing(tmp_path):
    """
    Test that create_directories does not fail if directories already exist.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Pre-create one directory
        os.makedirs("code", exist_ok=True)
        
        created = create_directories()
        
        # Should not include 'code' in the newly created list
        assert "code" not in created
        assert "data" in created
        assert "tests" in created
        
    finally:
        os.chdir(original_cwd)
