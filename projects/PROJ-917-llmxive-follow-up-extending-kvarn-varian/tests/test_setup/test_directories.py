"""
Unit Tests for Directory Initialization (Task T001a).

These tests verify that the project directory structure is correctly created
and that the setup module functions as expected.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_directories import create_directories, verify_structure, DIRECTORIES_TO_CREATE

class TestDirectoryCreation:
    """Tests for directory creation functionality."""

    def test_create_directories_creates_all_paths(self, tmp_path):
        """Verify that create_directories creates all specified subdirectories."""
        # Create temporary directories based on the template
        create_directories(tmp_path, DIRECTORIES_TO_CREATE)
        
        # Verify each directory exists
        for dir_path in DIRECTORIES_TO_CREATE:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_create_directories_handles_existing(self, tmp_path):
        """Verify that create_directories does not fail if directories already exist."""
        # Create the structure once
        create_directories(tmp_path, DIRECTORIES_TO_CREATE)
        
        # Create again - should not raise
        create_directories(tmp_path, DIRECTORIES_TO_CREATE)
        
        # Verify still exists
        assert (tmp_path / "code").exists()

    def test_create_directories_creates_parents(self, tmp_path):
        """Verify that nested directories are created even if parents don't exist."""
        # Explicitly test a nested path
        nested_path = "code/data_generation/special"
        create_directories(tmp_path, [nested_path])
        
        full_path = tmp_path / nested_path
        assert full_path.exists()
        assert full_path.is_dir()

class TestDirectoryVerification:
    """Tests for directory verification functionality."""

    def test_verify_structure_returns_true_when_all_exist(self, tmp_path):
        """Verify that verify_structure returns True when all directories exist."""
        create_directories(tmp_path, DIRECTORIES_TO_CREATE)
        assert verify_structure(tmp_path, DIRECTORIES_TO_CREATE) is True

    def test_verify_structure_returns_false_when_missing(self, tmp_path):
        """Verify that verify_structure returns False when a directory is missing."""
        # Create only one directory
        (tmp_path / "code").mkdir()
        
        # Check against full list - should fail
        assert verify_structure(tmp_path, DIRECTORIES_TO_CREATE) is False

    def test_verify_structure_with_empty_list(self, tmp_path):
        """Verify that verify_structure returns True for an empty list."""
        assert verify_structure(tmp_path, []) is True

class TestIntegration:
    """Integration tests for the full setup flow."""

    def test_full_setup_flow(self, tmp_path):
        """Test the complete flow: create then verify."""
        # Simulate the main function logic
        create_directories(tmp_path, DIRECTORIES_TO_CREATE)
        success = verify_structure(tmp_path, DIRECTORIES_TO_CREATE)
        
        assert success is True
        
        # Verify specific expected paths
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "code" / "simulation").exists()
        assert (tmp_path / "tests").exists()