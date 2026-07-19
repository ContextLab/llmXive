"""
Unit tests for the project structure initialization logic.

These tests verify that the directory creation logic works correctly
and handles edge cases appropriately.
"""

import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the function to test
from setup_structure import create_directory_structure


class TestDirectoryCreation:
    """Test cases for create_directory_structure function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
            "contracts"
        ]

        created_paths = create_directory_structure(tmp_path)

        for dir_name in required_dirs:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"

    def test_creates_nested_directories(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        nested_dirs = ["data/raw", "data/processed", "data/results"]

        created_paths = create_directory_structure(tmp_path)

        for dir_name in nested_dirs:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Nested directory {expected_path} was not created"

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the function handles existing directories gracefully."""
        # Pre-create some directories
        pre_created = tmp_path / "code"
        pre_created.mkdir()

        # Run the function
        created_paths = create_directory_structure(tmp_path)

        # Should not raise an error and should return the path
        assert pre_created in created_paths
        assert pre_created.exists()

    def test_creates_init_files_for_packages(self, tmp_path):
        """Verify that __init__.py files are created for 'code' and 'tests' directories."""
        created_paths = create_directory_structure(tmp_path)

        code_dir = tmp_path / "code"
        tests_dir = tmp_path / "tests"

        code_init = code_dir / "__init__.py"
        tests_init = tests_dir / "__init__.py"

        assert code_init.exists(), "__init__.py should be created in 'code' directory"
        assert tests_init.exists(), "__init__.py should be created in 'tests' directory"

    def test_returns_list_of_created_paths(self, tmp_path):
        """Verify that the function returns a list of Path objects."""
        result = create_directory_structure(tmp_path)

        assert isinstance(result, list), "Function should return a list"
        assert len(result) > 0, "List should not be empty"

        for path in result:
            assert isinstance(path, Path), "Each item should be a Path object"
            assert path.exists(), f"Path {path} should exist"

    def test_relative_path_handling(self, tmp_path):
        """Verify that paths are correctly constructed relative to the provided root."""
        test_root = tmp_path / "custom_root"
        test_root.mkdir()

        created_paths = create_directory_structure(test_root)

        for path in created_paths:
            # All paths should be under the custom root
            assert str(path).startswith(str(test_root)), f"Path {path} is not under {test_root}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])