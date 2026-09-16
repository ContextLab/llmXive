import os
import pytest
import tempfile
import shutil

# Import the module under test
from setup_data_dirs import create_directories, DATA_DIRS

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_directories_structure(temp_project_root):
    """Test that create_directories creates all required subdirectories."""
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run the function
        create_directories(".")
        
        # Verify each directory exists
        for dir_name in DATA_DIRS:
            full_path = os.path.join(temp_project_root, dir_name)
            assert os.path.exists(full_path), f"Directory {dir_name} was not created"
            assert os.path.isdir(full_path), f"{dir_name} is not a directory"
    finally:
        os.chdir(original_cwd)

def test_create_directories_idempotent(temp_project_root):
    """Test that running create_directories multiple times does not raise errors."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run twice
        create_directories(".")
        create_directories(".")
        
        # Verify structure is intact
        for dir_name in DATA_DIRS:
            full_path = os.path.join(temp_project_root, dir_name)
            assert os.path.isdir(full_path)
    finally:
        os.chdir(original_cwd)
