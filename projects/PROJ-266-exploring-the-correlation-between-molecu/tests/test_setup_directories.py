import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Mock the project root for testing if necessary, or rely on the actual get_project_root
# For this test, we assume the test runner is executed from the project root
# or that get_project_root correctly identifies the root.

from utils.config import get_project_root
from code.data.setup_directories import create_directories, verify_directories

def test_directory_creation():
    """
    Test that create_directories actually creates the required folders.
    """
    project_root = get_project_root()
    
    # Clean up if they exist from previous runs (optional, but good for isolation)
    # Note: In a real CI environment, we might not want to delete data, 
    # but for unit testing the logic, we ensure the function creates them.
    
    create_directories()
    
    # Assertions matching T008a requirements
    assert os.path.isdir(project_root / "data" / "raw"), "data/raw/ missing"
    assert os.path.isdir(project_root / "data" / "processed"), "data/processed/ missing"
    assert os.path.isdir(project_root / "state" / "projects"), "state/projects/ missing"
    assert os.path.isdir(project_root / "state" / "pending"), "state/pending/ missing"

def test_directory_verification():
    """
    Test that verify_directories passes when directories exist.
    """
    project_root = get_project_root()
    
    # Ensure they exist first
    create_directories()
    
    # This should not raise an AssertionError
    try:
        verify_directories()
    except AssertionError as e:
        pytest.fail(f"verify_directories failed unexpectedly: {e}")

def test_verify_directories_fails_when_missing():
    """
    Test that verify_directories raises AssertionError if a directory is missing.
    """
    project_root = get_project_root()
    
    # Temporarily remove a directory to test failure
    temp_path = project_root / "data" / "raw"
    if temp_path.exists():
        shutil.rmtree(temp_path)
    
    with pytest.raises(AssertionError):
        verify_directories()
    
    # Restore for subsequent tests
    temp_path.mkdir(parents=True, exist_ok=True)