"""
Unit tests for Task T001c: data/interim directory creation and verification.

These tests verify that the setup script correctly creates and validates
the 'data/interim' directory structure.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_interim_directory import create_interim_directory, verify_interim_directory

class TestInterimDirectory:
    """Test suite for interim directory operations."""

    def test_create_directory_when_not_exists(self, tmp_path):
        """Test that create_interim_directory creates the directory if it doesn't exist."""
        data_dir = tmp_path / "data"
        interim_dir = data_dir / "interim"
        
        assert not interim_dir.exists(), "Test setup failed: interim dir should not exist initially"
        
        result = create_interim_directory(tmp_path)
        
        assert result is True, "create_interim_directory should return True on success"
        assert interim_dir.exists(), "Directory should exist after creation"
        assert interim_dir.is_dir(), "Path should be a directory"

    def test_create_directory_when_exists(self, tmp_path):
        """Test that create_interim_directory returns True if directory already exists."""
        data_dir = tmp_path / "data"
        interim_dir = data_dir / "interim"
        
        # Create the directory first
        interim_dir.mkdir(parents=True)
        
        result = create_interim_directory(tmp_path)
        
        assert result is True, "create_interim_directory should return True if dir exists"
        assert interim_dir.exists(), "Directory should still exist"

    def test_verify_directory_when_exists(self, tmp_path):
        """Test that verify_interim_directory returns True if directory exists."""
        data_dir = tmp_path / "data"
        interim_dir = data_dir / "interim"
        interim_dir.mkdir(parents=True)
        
        result = verify_interim_directory(tmp_path)
        
        assert result is True, "verify_interim_directory should return True if dir exists"

    def test_verify_directory_when_not_exists(self, tmp_path):
        """Test that verify_interim_directory returns False if directory doesn't exist."""
        # Ensure directory does not exist
        data_dir = tmp_path / "data"
        # Do not create interim
        
        result = verify_interim_directory(tmp_path)
        
        assert result is False, "verify_interim_directory should return False if dir missing"

    def test_verify_directory_is_file_not_dir(self, tmp_path):
        """Test that verify_interim_directory returns False if path is a file, not a directory."""
        data_dir = tmp_path / "data"
        interim_dir = data_dir / "interim"
        
        # Create as a file
        interim_dir.touch()
        
        result = verify_interim_directory(tmp_path)
        
        assert result is False, "verify_interim_directory should return False if path is a file"
        assert not interim_dir.is_dir(), "Path should not be a directory"

    def test_creates_parent_directories(self, tmp_path):
        """Test that the function creates parent 'data' directory if missing."""
        data_dir = tmp_path / "data"
        interim_dir = data_dir / "interim"
        
        assert not data_dir.exists(), "Test setup failed: data dir should not exist"
        
        result = create_interim_directory(tmp_path)
        
        assert result is True
        assert data_dir.exists(), "Parent 'data' directory should be created"
        assert data_dir.is_dir(), "Parent 'data' should be a directory"
        assert interim_dir.exists(), "Child 'interim' directory should be created"