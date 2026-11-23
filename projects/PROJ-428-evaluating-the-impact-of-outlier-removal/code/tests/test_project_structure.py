import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path so we can import from src
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.setup_dirs import setup_directories

def get_project_root():
    """Get the project root directory (parent of code/)"""
    return Path(__file__).resolve().parent.parent.parent

def test_required_directories_exist():
    """Test that setup_directories creates all required directories"""
    project_root = get_project_root()
    
    # Run the setup
    created_dirs = setup_directories()
    
    # Verify each directory exists
    expected_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "state"
    ]
    
    for expected_dir in expected_dirs:
        assert expected_dir.exists(), f"Directory does not exist: {expected_dir}"
        assert expected_dir.is_dir(), f"Path is not a directory: {expected_dir}"
    
    # Verify the returned list matches expected directories
    assert len(created_dirs) == len(expected_dirs)
    for dir1, dir2 in zip(sorted(created_dirs), sorted(expected_dirs)):
        assert dir1 == dir2

def test_project_root_is_writable():
    """Test that the project root is writable"""
    project_root = get_project_root()
    
    # Try to create a temporary file in the project root
    test_file = project_root / ".test_writable"
    try:
        test_file.touch()
        assert test_file.exists(), "Could not create test file in project root"
        assert os.access(test_file, os.W_OK), "Project root is not writable"
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()