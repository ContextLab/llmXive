import os
import pytest
from pathlib import Path
import shutil

# Adjust import based on how tests are run (usually PYTHONPATH includes root)
from code.setup_dirs import create_directory

def test_create_directory_new():
    """Test that create_directory creates a new directory."""
    test_path = Path("data/test_new_dir_temp")
    
    # Cleanup if exists
    if test_path.exists():
        shutil.rmtree(test_path)
        
    create_directory(str(test_path))
    
    assert test_path.exists(), f"Directory {test_path} was not created"
    assert test_path.is_dir(), f"{test_path} is not a directory"
    
    # Cleanup
    shutil.rmtree(test_path)

def test_create_directory_exists():
    """Test that create_directory does not error if directory exists."""
    test_path = Path("data/test_exists_dir_temp")
    
    # Ensure it exists first
    test_path.mkdir(parents=True, exist_ok=True)
    
    # Should not raise
    create_directory(str(test_path))
    
    assert test_path.exists()
    
    # Cleanup
    shutil.rmtree(test_path)

def test_create_nested_directory():
    """Test that create_directory creates parent directories."""
    test_path = Path("data/nested/test_deep_dir_temp")
    
    # Cleanup if exists
    if test_path.parent.exists():
        shutil.rmtree(test_path.parent)
        
    create_directory(str(test_path))
    
    assert test_path.exists()
    assert test_path.parent.exists()
    
    # Cleanup
    shutil.rmtree(test_path.parent)