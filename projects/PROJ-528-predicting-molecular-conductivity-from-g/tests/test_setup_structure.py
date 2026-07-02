"""
Tests for project structure initialization.
"""
import os
import tempfile
import pytest
from code.setup_structure import create_project_structure


class TestProjectStructure:
    """Test suite for create_project_structure function."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_project_structure(tmpdir)

            assert result is True

            required_dirs = [
                "code",
                "tests",
                "data/raw",
                "data/processed",
                "contracts",
                "docs"
            ]

            for dir_name in required_dirs:
                full_path = os.path.join(tmpdir, dir_name)
                assert os.path.isdir(full_path), f"Directory {dir_name} was not created"

    def test_handles_existing_directories(self):
        """Verify that the function handles pre-existing directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-create one directory
            existing_dir = os.path.join(tmpdir, "code")
            os.makedirs(existing_dir)

            result = create_project_structure(tmpdir)

            assert result is True
            assert os.path.isdir(existing_dir)

    def test_nested_directories_created(self):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_project_structure(tmpdir)

            assert result is True

            nested_dirs = [
                "data/raw",
                "data/processed"
            ]

            for dir_name in nested_dirs:
                full_path = os.path.join(tmpdir, dir_name)
                assert os.path.isdir(full_path), f"Nested directory {dir_name} was not created"