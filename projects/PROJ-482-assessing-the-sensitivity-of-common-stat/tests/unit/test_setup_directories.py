import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_directories
sys.path.insert(0, 'code')
from setup_directories import ensure_dir

def test_ensure_dir_creates_new_directory():
    """Test that ensure_dir creates a new directory that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "test_new_dir")
        assert not os.path.exists(test_path)
        
        result = ensure_dir(test_path)
        
        assert result is True
        assert os.path.exists(test_path)
        assert os.path.isdir(test_path)
        # Check for .gitkeep
        assert os.path.exists(os.path.join(test_path, ".gitkeep"))

def test_ensure_dir_existing_directory():
    """Test that ensure_dir returns True for an existing directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Directory already exists
        assert os.path.exists(tmpdir)
        
        result = ensure_dir(tmpdir)
        
        assert result is True
        assert os.path.isdir(tmpdir)

def test_ensure_dir_creates_nested_directories():
    """Test that ensure_dir creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "parent", "child", "grandchild")
        assert not os.path.exists(test_path)
        
        result = ensure_dir(test_path)
        
        assert result is True
        assert os.path.exists(test_path)
        assert os.path.exists(os.path.join(test_path, ".gitkeep"))