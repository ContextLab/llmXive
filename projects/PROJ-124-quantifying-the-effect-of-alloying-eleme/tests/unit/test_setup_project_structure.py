"""
Unit tests for the project structure initialization script.
Verifies that all required directories are created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project_structure import create_project_structure


class TestProjectStructure:
    """Test cases for project structure creation."""

    def test_all_required_directories_created(self, tmp_path):
        """Test that all required directories are created."""
        # Define expected directories
        expected_dirs = [
            "code/data", "code/models", "code/utils", "code/config",
            "data/raw", "data/processed",
            "state", "output",
            "tests/contract", "tests/integration", "tests/unit",
            "docs/paper", "docs/reports"
        ]

        # Create the project structure
        create_project_structure(str(tmp_path))

        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_nested_directories_created(self, tmp_path):
        """Test that nested directory structures are created correctly."""
        # Create the structure
        create_project_structure(str(tmp_path))

        # Verify nested paths exist
        nested_paths = [
            "code/data", "code/models", "code/utils", "code/config",
            "tests/contract", "tests/integration", "tests/unit",
            "docs/paper", "docs/reports"
        ]

        for path in nested_paths:
            full_path = tmp_path / path
            assert full_path.exists(), f"Nested directory {path} was not created"

    def test_idempotent_creation(self, tmp_path):
        """Test that running the function multiple times doesn't cause errors."""
        # Run twice
        create_project_structure(str(tmp_path))
        create_project_structure(str(tmp_path))

        # Verify directories still exist
        expected_dirs = [
            "code/data", "data/raw", "state", "output",
            "tests/unit", "docs/paper"
        ]

        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists() and full_path.is_dir()

    def test_directory_permissions(self, tmp_path):
        """Test that created directories have correct permissions."""
        create_project_structure(str(tmp_path))

        # Check that directories are writable
        test_dir = tmp_path / "code" / "data"
        assert os.access(test_dir, os.W_OK), "Created directory is not writable"