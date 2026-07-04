"""
Tests for the create_processed_directory script.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from create_processed_directory import ensure_processed_directory

def test_ensure_processed_directory_creates_dir():
    """Test that the function creates the directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Ensure 'data' exists but 'processed' does not
        data_dir = root / "data"
        data_dir.mkdir()
        processed_dir = root / "data" / "processed"
        
        assert not processed_dir.exists()
        
        result = ensure_processed_directory(root)
        
        assert result.exists()
        assert result.is_dir()
        assert result == processed_dir

def test_ensure_processed_directory_exists():
    """Test that the function works if directory already exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        processed_dir = root / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        result = ensure_processed_directory(root)
        
        assert result.exists()
        assert result.is_dir()
        assert result == processed_dir