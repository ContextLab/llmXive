"""
Tests for the setup_directories module to ensure the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the parent directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_directories import main

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path)

def test_directory_structure_creation(temp_dir):
    """Test that all required directories are created."""
    # Change to the temp directory to simulate the project root
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Run the main function
        result = main()
        
        # Verify the function returned success
        assert result == 0, "main() should return 0 on success"
        
        # Define expected directories
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code/src",
            "code/tests",
            "code/notebooks",
            "paper",
            "state",
            "contracts"
        ]
        
        # Check each directory exists
        for dir_name in expected_dirs:
            full_path = Path(temp_dir) / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"Path {dir_name} exists but is not a directory"
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_no_overwrite_existing_files(temp_dir):
    """Test that the script handles existing directories gracefully."""
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Pre-create one of the required directories
        pre_created = Path(temp_dir) / "paper"
        pre_created.mkdir(parents=True, exist_ok=True)
        
        # Run main
        result = main()
        
        # Should still succeed
        assert result == 0
        
        # Verify the directory is still a directory (not a file)
        assert pre_created.is_dir()
        
    finally:
        os.chdir(original_cwd)
