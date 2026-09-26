"""
Unit tests for the data directory creation functionality.

Tests task T001c: Verify that the required data directories are created.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_setup.create_data_dirs import create_data_directories

class TestDataDirectoryCreation:
    """Test cases for data directory creation."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required data directories are created."""
        # Define expected directories
        expected_dirs = [
            "data",
            "data/raw",
            "data/derived",
            "data/aggregated"
        ]
        
        # Create directories
        create_data_directories(tmp_path)
        
        # Verify each directory exists
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_handles_existing_directories(self, tmp_path):
        """Test that existing directories are not recreated or cause errors."""
        # Pre-create some directories
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        # This should not raise an exception
        create_data_directories(tmp_path)
        
        # Verify they still exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        # Don't create any directories beforehand
        # This should create the entire tree
        create_data_directories(tmp_path)
        
        # Verify the deepest directory exists
        assert (tmp_path / "data" / "aggregated").exists()
        assert (tmp_path / "data" / "aggregated").is_dir()

    def test_creates_nested_structure(self, tmp_path):
        """Test that the complete nested structure is created correctly."""
        create_data_directories(tmp_path)
        
        # Verify the complete structure
        structure = [
            "data",
            "data/raw",
            "data/derived",
            "data/aggregated"
        ]
        
        for path in structure:
            full_path = tmp_path / path
            assert full_path.exists(), f"Missing: {path}"
            assert full_path.is_dir(), f"Not a directory: {path}"
