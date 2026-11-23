import os
import pytest
from setup_project_structure import ensure_directory, create_init_file

def test_ensure_directory_creates_new():
    """Test that ensure_directory creates a new directory."""
    test_path = "tests/test_temp_dir_12345"
    # Ensure it doesn't exist first
    if os.path.exists(test_path):
        os.remove(test_path) if os.path.isfile(test_path) else os.rmdir(test_path)
    
    ensure_directory(test_path)
    assert os.path.exists(test_path)
    assert os.isdir(test_path)
    
    # Cleanup
    os.rmdir(test_path)

def test_ensure_directory_existing():
    """Test that ensure_directory doesn't error on existing dir."""
    test_path = "tests"
    ensure_directory(test_path)
    assert os.path.exists(test_path)

def test_create_init_file_creates_new():
    """Test that create_init_file creates a new file."""
    test_path = "tests/test_temp_init_12345.py"
    if os.path.exists(test_path):
        os.remove(test_path)
    
    create_init_file(test_path)
    assert os.path.exists(test_path)
    assert os.path.isfile(test_path)
    
    # Check file is empty
    with open(test_path, 'r') as f:
        content = f.read()
    assert content == ""
    
    # Cleanup
    os.remove(test_path)

def test_create_init_file_existing():
    """Test that create_init_file doesn't error on existing file."""
    test_path = "tests/__init__.py"
    create_init_file(test_path)
    assert os.path.exists(test_path)