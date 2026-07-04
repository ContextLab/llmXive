"""
Unit tests for the setup_directories.py script.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest

# Import the function to test
# We need to adjust the import path or run this test from the project root
# Assuming the test runner adds the project root to sys.path
try:
    from setup_directories import ensure_directories, DIRECTORIES
except ImportError:
    # Fallback if running from code/ or similar
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from setup_directories import ensure_directories, DIRECTORIES

def test_ensure_directories_creates_missing(tmp_path):
    """Test that ensure_directories creates missing directories."""
    # Temporarily override PROJECT_ROOT for the test
    import setup_directories
    original_root = setup_directories.PROJECT_ROOT
    setup_directories.PROJECT_ROOT = str(tmp_path)
    
    # Manually construct the expected paths for this temp directory
    test_dirs = [
        os.path.join(str(tmp_path), "data", "raw"),
        os.path.join(str(tmp_path), "data", "processed"),
        os.path.join(str(tmp_path), "results"),
        os.path.join(str(tmp_path), "results", "plots"),
    ]
    
    # Verify they don't exist yet
    for d in test_dirs:
        assert not os.path.exists(d), f"Directory {d} should not exist before test"
    
    # Run the function
    result = ensure_directories()
    
    # Verify result is True
    assert result is True, "ensure_directories should return True on success"
    
    # Verify directories exist
    for d in test_dirs:
        assert os.path.exists(d), f"Directory {d} should exist after running ensure_directories"
        assert os.path.isdir(d), f"{d} should be a directory"
    
    # Restore original root
    setup_directories.PROJECT_ROOT = original_root

def test_ensure_directories_skips_existing(tmp_path):
    """Test that ensure_directories handles existing directories gracefully."""
    import setup_directories
    original_root = setup_directories.PROJECT_ROOT
    setup_directories.PROJECT_ROOT = str(tmp_path)
    
    # Pre-create some directories
    pre_created = os.path.join(str(tmp_path), "data", "raw")
    os.makedirs(pre_created, exist_ok=True)
    
    # Run the function
    result = ensure_directories()
    
    assert result is True
    assert os.path.exists(pre_created)
    
    setup_directories.PROJECT_ROOT = original_root