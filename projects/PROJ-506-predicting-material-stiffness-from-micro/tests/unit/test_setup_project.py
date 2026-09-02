import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from setup_project import create_directories, create_init_files, check_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates all required directories."""
    created = create_directories(temp_project_root)
    
    # Check that the correct number of directories were created
    expected_count = 10
    assert len(created) == expected_count, f"Expected {expected_count} directories, got {len(created)}"
    
    # Check specific directories exist
    required_dirs = [
        "code/data_generation",
        "code/training",
        "data/raw",
        "tests/unit",
        "specs/001-predict-stiffness-cnn/contracts"
    ]
    
    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_create_init_files(temp_project_root):
    """Test that create_init_files creates all required __init__.py files."""
    # First create directories
    create_directories(temp_project_root)
    
    created = create_init_files(temp_project_root)
    
    # Check that the correct number of files were created
    expected_count = 9
    assert len(created) == expected_count, f"Expected {expected_count} files, got {len(created)}"
    
    # Check specific files exist
    required_files = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py"
    ]
    
    for file_path in required_files:
        full_path = temp_project_root / file_path
        assert full_path.exists(), f"File {file_path} was not created"
        assert full_path.is_file(), f"{file_path} is not a file"

def test_check_structure_success(temp_project_root):
    """Test check_structure returns success when all directories exist."""
    create_directories(temp_project_root)
    
    success, missing = check_structure(temp_project_root)
    
    assert success is True, "check_structure should return True when all directories exist"
    assert len(missing) == 0, f"No directories should be missing, but found: {missing}"

def test_check_structure_failure(temp_project_root):
    """Test check_structure returns failure when directories are missing."""
    # Don't create any directories
    
    success, missing = check_structure(temp_project_root)
    
    assert success is False, "check_structure should return False when directories are missing"
    assert len(missing) > 0, "Should report missing directories"
    assert "code/data_generation" in missing, "Should report code/data_generation as missing"
