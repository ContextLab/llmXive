"""
Unit tests for directory verification logic (T008c).
"""
import os
import tempfile
from pathlib import Path
import pytest

# Mock the config module to use a temporary directory
import sys
from unittest.mock import patch

@pytest.fixture
def temp_project_root():
    """Create a temporary project root with required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create required directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        yield tmp_path

def test_verify_directories_success(temp_project_root):
    """Test that verification passes when directories exist."""
    with patch('code.data.verify_directories.get_project_root', return_value=temp_project_root):
        from code.data.verify_directories import verify_directories
        
        result = verify_directories()
        assert result is True

def test_verify_directories_missing_raw(temp_project_root):
    """Test that verification fails when data/raw is missing."""
    # Remove the raw directory
    (temp_project_root / "data" / "raw").rmdir()
    
    with patch('code.data.verify_directories.get_project_root', return_value=temp_project_root):
        from code.data.verify_directories import verify_directories
        
        result = verify_directories()
        assert result is False

def test_verify_directories_missing_processed(temp_project_root):
    """Test that verification fails when data/processed is missing."""
    # Remove the processed directory
    (temp_project_root / "data" / "processed").rmdir()
    
    with patch('code.data.verify_directories.get_project_root', return_value=temp_project_root):
        from code.data.verify_directories import verify_directories
        
        result = verify_directories()
        assert result is False

def test_verify_directories_both_missing(temp_project_root):
    """Test that verification fails when both directories are missing."""
    # Remove both directories
    (temp_project_root / "data" / "raw").rmdir()
    (temp_project_root / "data" / "processed").rmdir()
    
    with patch('code.data.verify_directories.get_project_root', return_value=temp_project_root):
        from code.data.verify_directories import verify_directories
        
        result = verify_directories()
        assert result is False