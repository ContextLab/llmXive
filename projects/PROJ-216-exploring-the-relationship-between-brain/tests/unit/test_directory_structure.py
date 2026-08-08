"""
Unit tests to verify the project directory structure and __init__.py files.
Satisfies the verification requirement for Task T001.
"""
import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path to import setup_directories if needed, 
# though we are testing the file system state directly.
# The script code/setup_directories.py is expected to have run or be runnable.

class TestDirectoryStructure:
    """Tests for verifying the initialized project directory structure."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Determine the project root path for tests.
        Assumes this file is at tests/unit/test_directory_structure.py
        """
        current_file = Path(__file__).resolve()
        self.project_root = current_file.parent.parent.parent

    def test_data_raw_exists(self):
        """Verify data/raw directory exists."""
        path = self.project_root / "data" / "raw"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_data_interim_exists(self):
        """Verify data/interim directory exists."""
        path = self.project_root / "data" / "interim"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_data_processed_exists(self):
        """Verify data/processed directory exists."""
        path = self.project_root / "data" / "processed"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_code_dir_exists(self):
        """Verify code directory exists."""
        path = self.project_root / "code"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_tests_unit_exists(self):
        """Verify tests/unit directory exists."""
        path = self.project_root / "tests" / "unit"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_tests_integration_exists(self):
        """Verify tests/integration directory exists."""
        path = self.project_root / "tests" / "integration"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_reports_exists(self):
        """Verify reports directory exists."""
        path = self.project_root / "reports"
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

    def test_code_init_exists(self):
        """Verify code/__init__.py exists."""
        path = self.project_root / "code" / "__init__.py"
        assert path.exists(), f"File {path} does not exist"
        assert path.is_file(), f"{path} is not a file"

    def test_tests_init_exists(self):
        """Verify tests/__init__.py exists."""
        path = self.project_root / "tests" / "__init__.py"
        assert path.exists(), f"File {path} does not exist"
        assert path.is_file(), f"{path} is not a file"

    def test_tests_unit_init_exists(self):
        """Verify tests/unit/__init__.py exists."""
        path = self.project_root / "tests" / "unit" / "__init__.py"
        assert path.exists(), f"File {path} does not exist"
        assert path.is_file(), f"{path} is not a file"

    def test_tests_integration_init_exists(self):
        """Verify tests/integration/__init__.py exists."""
        path = self.project_root / "tests" / "integration" / "__init__.py"
        assert path.exists(), f"File {path} does not exist"
        assert path.is_file(), f"{path} is not a file"