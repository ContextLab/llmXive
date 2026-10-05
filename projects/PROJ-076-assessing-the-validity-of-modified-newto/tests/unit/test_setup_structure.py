"""
Unit tests for the project directory structure creation (T001a).
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to import the function we are testing
# Since setup_structure.py is in code/, we need to adjust the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import create_directories


class TestCreateDirectories:
    """Test cases for directory creation functionality."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Change to temp directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            created_dirs = create_directories()

            # Check that all required directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results",
                "tests",
                "state",
                "code/models",
                "code/utils",
                "code/simulations",
            ]

            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_creates_init_files(self, tmp_path):
        """Test that __init__.py files are created in Python package directories."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            create_directories()

            init_dirs = [
                "code",
                "tests",
                "code/models",
                "code/utils",
                "code/simulations",
            ]

            for dir_name in init_dirs:
                init_file = tmp_path / dir_name / "__init__.py"
                assert init_file.exists(), f"__init__.py missing in {dir_name}"

        finally:
            os.chdir(original_cwd)

    def test_creates_data_readmes(self, tmp_path):
        """Test that README files are created in data directories."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            create_directories()

            for dir_name in ["data/raw", "data/processed"]:
                readme_file = tmp_path / dir_name / "README.md"
                assert readme_file.exists(), f"README.md missing in {dir_name}"
                # Check that it has content
                content = readme_file.read_text()
                assert len(content) > 0, f"README.md in {dir_name} is empty"

        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        """Test that running twice doesn't cause errors or duplicates."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            # Run twice
            create_directories()
            create_directories()

            # All directories should still exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results",
                "tests",
                "state",
            ]

            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} missing after second run"

        finally:
            os.chdir(original_cwd)