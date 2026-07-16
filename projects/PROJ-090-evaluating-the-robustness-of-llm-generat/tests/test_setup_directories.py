"""
Unit tests for the directory setup script.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setup_directories import create_directories


class TestDirectoryCreation:
    """Test suite for directory creation functionality."""

    def test_creates_code_structure(self, tmp_path):
        """Verify that code/ and its subdirectories are created."""
        create_directories(tmp_path)

        assert (tmp_path / "code").is_dir()
        assert (tmp_path / "code" / "data").is_dir()
        assert (tmp_path / "code" / "model").is_dir()
        assert (tmp_path / "code" / "analysis").is_dir()
        assert (tmp_path / "code" / "utils").is_dir()

    def test_creates_data_structure(self, tmp_path):
        """Verify that data/ and its subdirectories are created."""
        create_directories(tmp_path)

        assert (tmp_path / "data").is_dir()
        assert (tmp_path / "data" / "raw").is_dir()
        assert (tmp_path / "data" / "processed").is_dir()
        assert (tmp_path / "data" / "logs").is_dir()
        assert (tmp_path / "data" / "config").is_dir()

    def test_creates_tests_structure(self, tmp_path):
        """Verify that tests/ and its subdirectories are created (Task T003)."""
        create_directories(tmp_path)

        assert (tmp_path / "tests").is_dir()
        assert (tmp_path / "tests" / "unit").is_dir()
        assert (tmp_path / "tests" / "contract").is_dir()

    def test_creates_docs_and_figures(self, tmp_path):
        """Verify that docs/ and figures/ directories are created."""
        create_directories(tmp_path)

        assert (tmp_path / "docs").is_dir()
        assert (tmp_path / "figures").is_dir()

    def test_creates_init_files(self, tmp_path):
        """Verify that __init__.py files are created for Python packages."""
        create_directories(tmp_path)

        # Check root package init
        assert (tmp_path / "code" / "__init__.py").exists()
        assert (tmp_path / "tests" / "__init__.py").exists()

        # Check sub-package inits
        assert (tmp_path / "code" / "data" / "__init__.py").exists()
        assert (tmp_path / "code" / "model" / "__init__.py").exists()
        assert (tmp_path / "code" / "analysis" / "__init__.py").exists()
        assert (tmp_path / "code" / "utils" / "__init__.py").exists()

        assert (tmp_path / "tests" / "unit" / "__init__.py").exists()
        assert (tmp_path / "tests" / "contract" / "__init__.py").exists()

    def test_idempotent_creation(self, tmp_path):
        """Verify that running the script twice does not cause errors."""
        create_directories(tmp_path)
        create_directories(tmp_path)  # Should not raise

        assert (tmp_path / "tests" / "unit").is_dir()
        assert (tmp_path / "tests" / "contract").is_dir()

    def test_specific_task_t003_requirements(self, tmp_path):
        """
        Specific verification for Task T003:
        Create `tests/`, `tests/unit/`, `tests/contract/` directories.
        """
        create_directories(tmp_path)

        # Verify the exact paths required by T003
        tests_dir = tmp_path / "tests"
        unit_dir = tmp_path / "tests" / "unit"
        contract_dir = tmp_path / "tests" / "contract"

        assert tests_dir.exists(), "tests/ directory missing"
        assert tests_dir.is_dir(), "tests/ is not a directory"

        assert unit_dir.exists(), "tests/unit/ directory missing"
        assert unit_dir.is_dir(), "tests/unit/ is not a directory"

        assert contract_dir.exists(), "tests/contract/ directory missing"
        assert contract_dir.is_dir(), "tests/contract/ is not a directory"
