import os
import tempfile
import shutil
import pytest
from code.setup_data_dirs import create_directories

def test_create_directories_structure():
    """Test that create_directories creates the expected directory structure."""
    # We run this in a temp directory to avoid cluttering the project root during tests
    # However, the function assumes paths relative to the project root.
    # For this unit test, we verify that the logic works by checking if the 
    # function creates the directories if they don't exist.
    
    # Since the function uses relative paths, we can't easily isolate it without 
    # mocking os.path or changing the working directory. 
    # Instead, we test that the function runs without error and creates the dirs.
    
    # Backup current directory
    original_cwd = os.getcwd()
    
    # Create a temp directory and switch to it
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    
    try:
        # Call the function
        create_directories()
        
        # Verify directories exist
        assert os.path.isdir("data"), "data directory missing"
        assert os.path.isdir("data/raw"), "data/raw directory missing"
        assert os.path.isdir("data/raw/synthetic_graphs"), "data/raw/synthetic_graphs missing"
        assert os.path.isdir("data/processed"), "data/processed missing"
        assert os.path.isdir("data/figures"), "data/figures missing"
        assert os.path.isdir("data/logs"), "data/logs missing"
    finally:
        # Restore original directory and cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_create_directories_idempotent():
    """Test that calling create_directories multiple times does not raise errors."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    
    try:
        # Call twice
        create_directories()
        create_directories()
        
        # Should still exist
        assert os.path.isdir("data/processed")
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
