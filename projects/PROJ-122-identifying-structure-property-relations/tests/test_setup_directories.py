"""
Unit tests for the setup_directories module.
Verifies that the directory creation logic works as expected.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the function from the code module
# Since the project structure might vary during testing, we add the code path
import sys
from pathlib import Path
current_dir = Path(__file__).parent.parent
code_path = current_dir / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_directories import create_directories

def test_create_directories_structure(tmp_path):
    """Test that create_directories creates the required folder structure."""
    # Change to a temporary directory to simulate a clean project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock the root path behavior by patching the function or running it in the temp dir
        # Since the function uses Path("."), changing cwd is sufficient
        create_directories()
        
        # Verify directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/features",
            "tests",
            "state/projects",
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
        
        # Verify nested structure
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "features").exists()
        assert (tmp_path / "state" / "projects").exists()
        
    finally:
        os.chdir(original_cwd)

def test_create_directories_idempotent(tmp_path):
    """Test that running create_directories multiple times does not fail."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run twice
        create_directories()
        create_directories()
        
        # Verify all still exist
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data" / "raw").exists()
    finally:
        os.chdir(original_cwd)