"""
Unit tests for the setup_directories module (T008a).
Verifies that data/raw and data/processed directories are created.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the get_project_root function to use a temporary directory
# so we don't depend on the actual project root during testing
class MockConfig:
    @staticmethod
    def get_project_root():
        return Path(tempfile.mkdtemp())

# We need to patch the import before importing the module
import sys
from unittest.mock import patch

def test_create_directories():
    """Test that create_directories creates the required folders."""
    # Create a temporary project root
    temp_root = Path(tempfile.mkdtemp())
    try:
        # Patch the get_project_root to return our temp root
        with patch('code.data.setup_directories.get_project_root', return_value=temp_root):
            from code.data.setup_directories import create_directories
            
            # Execute the function
            result = create_directories()
            
            # Verify return value
            assert result is True, "create_directories should return True on success"
            
            # Verify directories exist
            raw_dir = temp_root / "data" / "raw"
            processed_dir = temp_root / "data" / "processed"
            
            assert raw_dir.is_dir(), f"Directory {raw_dir} was not created"
            assert processed_dir.is_dir(), f"Directory {processed_dir} was not created"
            
    finally:
        # Cleanup
        shutil.rmtree(temp_root, ignore_errors=True)

def test_create_directories_idempotent():
    """Test that calling create_directories multiple times doesn't fail."""
    temp_root = Path(tempfile.mkdtemp())
    try:
        with patch('code.data.setup_directories.get_project_root', return_value=temp_root):
            from code.data.setup_directories import create_directories
            
            # Call twice
            result1 = create_directories()
            result2 = create_directories()
            
            assert result1 is True
            assert result2 is True
            
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)