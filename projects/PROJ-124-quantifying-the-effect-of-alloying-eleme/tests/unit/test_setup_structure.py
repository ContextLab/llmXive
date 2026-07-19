"""
Unit tests for project structure creation.

These tests verify that the setup scripts correctly create
the required directory structure.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to add the code directory to the path for imports
import sys
from pathlib import Path

# Get the project root (parent of the tests directory)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from setup_project_structure import create_project_structure


class TestProjectStructure:
    """Tests for the project structure creation logic."""

    def test_create_project_structure_creates_all_dirs(self, tmp_path):
        """Verify that create_project_structure creates all required directories."""
        # Change to temp directory for testing
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Run the setup
            result = create_project_structure()

            # Verify return value
            assert result is True

            # Verify critical directories exist
            required_dirs = [
                "code/data", "code/models", "code/utils", "code/config",
                "data/raw", "data/processed", "state", "output",
                "tests/contract", "tests/integration", "tests/unit",
                "docs/paper", "docs/reports"
            ]

            for dir_name in required_dirs:
                full_path = tmp_path / dir_name
                assert full_path.exists(), f"Directory {dir_name} was not created"
                assert full_path.is_dir(), f"{dir_name} is not a directory"

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_create_project_structure_idempotent(self, tmp_path):
        """Verify that running the setup twice does not cause errors."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Run setup twice
            create_project_structure()
            result2 = create_project_structure()

            assert result2 is True

            # Verify directories still exist
            assert (tmp_path / "code/data").exists()
            assert (tmp_path / "state").exists()

        finally:
            os.chdir(original_cwd)

    def test_create_project_structure_handles_nested_paths(self, tmp_path):
        """Verify that nested directories like tests/contract are created."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            create_project_structure()

            # Check nested paths
            assert (tmp_path / "tests" / "contract").exists()
            assert (tmp_path / "tests" / "integration").exists()
            assert (tmp_path / "docs" / "paper").exists()

        finally:
            os.chdir(original_cwd)
