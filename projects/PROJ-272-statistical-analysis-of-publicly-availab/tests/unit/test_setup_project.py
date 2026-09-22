"""
Unit tests for the project setup utility.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import create_directory

def test_create_directory_new():
    """Test creating a new directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        relative_path = "test_new_dir/subdir"
        full_path = Path(tmpdir) / relative_path
        
        result = create_directory(tmpdir, relative_path)
        
        assert result is True
        assert full_path.exists()
        assert full_path.is_dir()

def test_create_directory_exists():
    """Test creating a directory that already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        relative_path = "test_existing_dir"
        full_path = Path(tmpdir) / relative_path
        
        # Create the directory first
        full_path.mkdir(parents=True)
        
        result = create_directory(tmpdir, relative_path)
        
        assert result is True
        assert full_path.exists()

def test_create_directory_nested():
    """Test creating nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        relative_path = "level1/level2/level3"
        full_path = Path(tmpdir) / relative_path
        
        result = create_directory(tmpdir, relative_path)
        
        assert result is True
        assert full_path.exists()
        assert (Path(tmpdir) / "level1").exists()
        assert (Path(tmpdir) / "level1" / "level2").exists()