"""
Tests for the project structure setup script.
Verifies that the required directories are created correctly.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from code.setup_project_structure import create_directories


class TestSetupProjectStructure:
    """Test cases for the create_directories function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "src",
            "data/raw",
            "data/derived",
            "data/annotations",
            "results",
            "tests",
            "specs"
        ]

        create_directories(tmp_path)

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_nested_directories_created_properly(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created with parents."""
        create_directories(tmp_path)

        # Check nested directory
        raw_data_dir = tmp_path / "data" / "raw"
        assert raw_data_dir.exists()
        assert raw_data_dir.is_dir()

        derived_data_dir = tmp_path / "data" / "derived"
        assert derived_data_dir.exists()
        assert derived_data_dir.is_dir()

        annotations_dir = tmp_path / "data" / "annotations"
        assert annotations_dir.exists()
        assert annotations_dir.is_dir()

    def test_does_not_fail_if_directories_exist(self, tmp_path):
        """Verify that the function doesn't fail if directories already exist."""
        # Pre-create some directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        # This should not raise an exception
        create_directories(tmp_path)

        # Verify they still exist
        assert (tmp_path / "src").exists()
        assert (tmp_path / "tests").exists()

    def test_creates_parent_directories_for_nested_paths(self, tmp_path):
        """Verify that parent directories are created when needed for nested paths."""
        # Start with an empty tmp_path (no data dir yet)
        assert not (tmp_path / "data").exists()

        create_directories(tmp_path)

        # Verify parent and child both exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "annotations").exists()

    def test_returns_nothing(self, tmp_path):
        """Verify that the function returns None."""
        result = create_directories(tmp_path)
        assert result is None

    def test_uses_current_directory_when_no_base_path_provided(self):
        """Verify that the function uses cwd when no base_path is provided."""
        with patch('code.setup_project_structure.Path') as mock_path:
            mock_instance = MagicMock()
            mock_path.return_value = mock_instance
            mock_instance.cwd.return_value = Path("/fake/cwd")

            # Call without arguments
            create_directories()

            # Verify cwd was called
            mock_path.cwd.assert_called_once()