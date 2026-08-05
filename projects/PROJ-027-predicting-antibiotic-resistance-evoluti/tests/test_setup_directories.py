"""
Tests for the setup_directories module (T001b).
Verifies that the correct directory structure is created and verified.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module functions
# Note: We need to adjust the import path if running from root or code dir
# Assuming tests are run from project root
try:
    from setup_directories import create_directories, verify_directories, DIRECTORIES_TO_CREATE
except ImportError:
    # Fallback for different execution contexts
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from setup_directories import create_directories, verify_directories, DIRECTORIES_TO_CREATE

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories actually creates the required folders."""
    # Verify they don't exist yet
    for d in DIRECTORIES_TO_CREATE:
        assert not (temp_project_root / d).exists()

    # Create them
    create_directories(temp_project_root, DIRECTORIES_TO_CREATE)

    # Verify they exist
    for d in DIRECTORIES_TO_CREATE:
        target = temp_project_root / d
        assert target.exists(), f"Directory {target} was not created."
        assert target.is_dir(), f"{target} exists but is not a directory."

def test_verify_directories_success(temp_project_root):
    """Test verify_directories returns True when all exist."""
    # Create them first
    create_directories(temp_project_root, DIRECTORIES_TO_CREATE)
    
    # Verify
    result = verify_directories(temp_project_root, DIRECTORIES_TO_CREATE)
    assert result is True, "Verification should return True when all directories exist."

def test_verify_directories_failure(temp_project_root):
    """Test verify_directories returns False when some are missing."""
    # Create only one
    create_directories(temp_project_root, ["code/utils"])
    
    # Verify should fail
    result = verify_directories(temp_project_root, DIRECTORIES_TO_CREATE)
    assert result is False, "Verification should return False when directories are missing."

def test_directory_structure_correct(temp_project_root):
    """Test that the specific paths required by T001b are created."""
    expected_paths = [
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/models"
    ]
    
    create_directories(temp_project_root, expected_paths)
    
    for path_str in expected_paths:
        p = temp_project_root / path_str
        assert p.exists(), f"Missing required path: {p}"
        assert p.is_dir(), f"Path is not a directory: {p}"