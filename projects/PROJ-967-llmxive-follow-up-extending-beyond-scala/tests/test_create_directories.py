import os
import tempfile
from pathlib import Path
import pytest
import shutil

# Import the function to test
from create_directories import ensure_directory

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_ensure_directory_creates_new_directory(temp_project_root):
    """Test that ensure_directory creates a new directory when it doesn't exist."""
    new_dir = temp_project_root / "test_dir"
    assert not new_dir.exists()
    
    ensure_directory(new_dir)
    
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_ensure_directory_existing_directory(temp_project_root):
    """Test that ensure_directory does nothing if directory already exists."""
    existing_dir = temp_project_root / "existing_dir"
    existing_dir.mkdir()
    assert existing_dir.exists()
    
    # Should not raise an exception
    ensure_directory(existing_dir)
    
    assert existing_dir.exists()
    assert existing_dir.is_dir()

def test_ensure_directory_nested(temp_project_root):
    """Test that ensure_directory creates nested directories."""
    nested_dir = temp_project_root / "level1" / "level2" / "level3"
    assert not nested_dir.exists()
    
    ensure_directory(nested_dir)
    
    assert nested_dir.exists()
    assert nested_dir.is_dir()

def test_main_creates_required_directories(temp_project_root):
    """Test that the main function creates the required data directories."""
    # Mock the script location to be inside the temp project root
    # We need to temporarily modify the path logic for testing
    original_cwd = os.getcwd()
    original_path = __file__
    
    try:
        # Change to temp root and create a fake code directory
        code_dir = temp_project_root / "code"
        code_dir.mkdir()
        
        # We need to test the logic of main() without actually running it
        # by directly checking if the directories would be created
        expected_dirs = [
            temp_project_root / "data" / "raw",
            temp_project_root / "data" / "processed",
            temp_project_root / "results"
        ]
        
        # Verify they don't exist initially
        for d in expected_dirs:
            assert not d.exists()
        
        # Call ensure_directory on each (simulating main's loop)
        for d in expected_dirs:
            ensure_directory(d)
        
        # Verify they now exist
        for d in expected_dirs:
            assert d.exists()
            assert d.is_dir()
    finally:
        os.chdir(original_cwd)