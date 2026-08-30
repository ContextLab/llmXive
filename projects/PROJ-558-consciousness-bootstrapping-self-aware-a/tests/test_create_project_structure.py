"""
Tests for the project structure creation script.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from code.create_project_structure import create_structure


class TestProjectStructureCreation:
    """Test cases for create_structure function."""

    def test_structure_created(self, tmp_path):
        """Test that the directory structure is created correctly."""
        # Change to temp directory to avoid cluttering real filesystem
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            base_dir = "test_project"
            create_structure(base_dir)

            project_path = Path(tmp_path) / base_dir

            # Verify base directory exists
            assert project_path.exists()
            assert project_path.is_dir()

            # Verify all required subdirectories exist
            required_subdirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "artifacts",
                "artifacts/checkpoints",
                "artifacts/reports",
            ]

            for subdir in required_subdirs:
                full_path = project_path / subdir
                assert full_path.exists(), f"Missing directory: {full_path}"
                assert full_path.is_dir(), f"Not a directory: {full_path}"

        finally:
            os.chdir(original_cwd)

    def test_existent_directory_no_error(self, tmp_path):
        """Test that calling create_structure on an existing directory does not raise an error."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            base_dir = "test_project"
            # Create it once
            create_structure(base_dir)
            # Create it again - should not raise
            create_structure(base_dir)

            project_path = Path(tmp_path) / base_dir
            assert project_path.exists()

        finally:
            os.chdir(original_cwd)
