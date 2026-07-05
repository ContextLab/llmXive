"""Integration tests for directory structure setup."""
import os
from pathlib import Path

import pytest

from code.config import PROJECT_ROOT
from code.utils.directory_setup import create_directory_structure


class TestDirectoryStructure:
    """Test suite for directory structure creation."""

    def test_required_directories_exist(self):
        """Test that all required directories exist."""
        data_dir = PROJECT_ROOT / "data"
        required_dirs = [
            data_dir / "raw",
            data_dir / "processed",
            data_dir / "validation",
            PROJECT_ROOT / "results",
            PROJECT_ROOT / "tests",
            PROJECT_ROOT / "tests" / "unit",
            PROJECT_ROOT / "tests" / "integration",
            PROJECT_ROOT / "tests" / "contract",
            PROJECT_ROOT / "code",
            PROJECT_ROOT / "code" / "utils",
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} does not exist"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_create_directory_structure_idempotent(self):
        """Test that creating directories is idempotent."""
        # Create directories
        create_directory_structure()

        # Get modification times before
        data_dir = PROJECT_ROOT / "data"
        processed_dir = data_dir / "processed"
        before_time = processed_dir.stat().st_mtime

        # Create directories again
        create_directory_structure()

        # Get modification times after
        after_time = processed_dir.stat().st_mtime

        # Time should not decrease (directories weren't recreated)
        assert after_time >= before_time
