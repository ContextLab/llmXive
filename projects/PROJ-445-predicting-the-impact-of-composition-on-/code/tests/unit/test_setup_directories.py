import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to path to allow imports if necessary, 
# though this test uses the function directly from the file path or relative import logic
# Assuming the test runner sets up the path or we import relative to the project root
# For this specific test file, we will import from the module assuming standard pytest discovery
# from setup_directories import create_directory_structure 
# Since the file is at code/setup_directories.py, we import relative to code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_directories import create_directory_structure

def test_create_directory_structure(tmp_path):
    """Test that create_directory_structure creates all required folders."""
    # Run the function
    create_directory_structure(str(tmp_path))
    
    # Define expected paths
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/residualized",
        "artifacts/models/lofo_models",
        "artifacts/figures",
        "state",
    ]
    
    # Verify existence
    for rel_path in expected_dirs:
        full_path = tmp_path / rel_path
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_create_directory_structure_idempotent(tmp_path):
    """Test that running the function twice does not cause errors."""
    create_directory_structure(str(tmp_path))
    # Run again
    create_directory_structure(str(tmp_path))
    
    # Verify one of the deep paths still exists
    assert (tmp_path / "data" / "raw").exists()