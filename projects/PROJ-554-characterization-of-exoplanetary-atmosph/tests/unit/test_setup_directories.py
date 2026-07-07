"""
Unit tests for the setup_directories module.
"""
import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the module under test
# We need to add the code directory to sys.path if running from tests
import sys
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_directories import create_directories, verify_directories, REQUIRED_DIRS

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_create_directories_creates_all_required(temp_project_root):
    """Test that create_directories creates all directories in REQUIRED_DIRS."""
    result = create_directories(temp_project_root)

    for dir_name in REQUIRED_DIRS:
        assert dir_name in result, f"Missing result for {dir_name}"
        assert result[dir_name]["exists"], f"Directory {dir_name} should exist after creation"
        assert result[dir_name]["created"] or (temp_project_root / dir_name).exists(), \
            f"Directory {dir_name} should be created or already exist"

        full_path = temp_project_root / dir_name
        assert full_path.exists(), f"Physical path {full_path} should exist"
        assert full_path.is_dir(), f"Physical path {full_path} should be a directory"

def test_verify_directories_returns_true_when_all_exist(temp_project_root):
    """Test that verify_directories returns True when all directories exist."""
    # First create them
    create_directories(temp_project_root)
    # Then verify
    assert verify_directories(temp_project_root) is True

def test_verify_directories_returns_false_when_missing(temp_project_root):
    """Test that verify_directories returns False if a directory is missing."""
    # Do not create directories
    assert verify_directories(temp_project_root) is False

def test_verify_directories_returns_false_if_not_directory(temp_project_root):
    """Test that verify_directories returns False if a path exists but is a file."""
    # Create a file where a directory should be
    dummy_file = temp_project_root / "code"
    dummy_file.touch()

    assert verify_directories(temp_project_root) is False
    # Cleanup
    dummy_file.unlink()