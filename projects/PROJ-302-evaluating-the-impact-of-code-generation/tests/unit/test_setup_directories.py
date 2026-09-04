"""
Unit tests for the setup_directories module.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module under test
from setup_directories import create_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_core_directories_created(temp_project_root):
    """Test that core directories are created."""
    # Run the directory creation
    create_directories()
    
    # Check that core directories exist
    core_dirs = ["code", "data", "tests", "docs"]
    for dir_name in core_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_data_subdirectories_created(temp_project_root):
    """Test that data subdirectories are created."""
    create_directories()
    
    data_subdirs = ["data/raw", "data/processed"]
    for dir_path_str in data_subdirs:
        dir_path = temp_project_root / dir_path_str
        assert dir_path.exists(), f"Directory {dir_path_str} was not created"
        assert dir_path.is_dir(), f"{dir_path_str} exists but is not a directory"

def test_code_subdirectories_created(temp_project_root):
    """Test that code subdirectories are created."""
    create_directories()
    
    code_subdirs = [
        "code/data_acquisition",
        "code/feature_extraction",
        "code/analysis",
        "code/utils"
    ]
    for dir_path_str in code_subdirs:
        dir_path = temp_project_root / dir_path_str
        assert dir_path.exists(), f"Directory {dir_path_str} was not created"
        assert dir_path.is_dir(), f"{dir_path_str} exists but is not a directory"

def test_idempotency(temp_project_root):
    """Test that running the script twice doesn't cause errors."""
    # Run twice
    create_directories()
    create_directories()
    
    # Verify directories still exist
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "data").exists()
    assert (temp_project_root / "tests").exists()
    assert (temp_project_root / "docs").exists()

def test_nested_directories_created(temp_project_root):
    """Test that nested directories are created with parents=True."""
    create_directories()
    
    # Check a deeply nested directory
    nested_dir = temp_project_root / "code" / "data_acquisition"
    assert nested_dir.exists()
    assert nested_dir.is_dir()