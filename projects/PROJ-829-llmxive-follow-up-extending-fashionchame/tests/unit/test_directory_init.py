"""
Unit tests for directory initialization.

These tests verify that the project structure is correctly set up.
"""
import pytest
from pathlib import Path
import sys

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))


class TestDirectoryInitialization:
    """Test cases for directory initialization."""

    def test_tests_directory_has_init_file(self):
        """Verify that tests/__init__.py exists."""
        tests_dir = Path(__file__).parent.parent
        init_file = tests_dir / "__init__.py"
        assert init_file.exists(), "tests/__init__.py should exist"
        assert init_file.is_file(), "tests/__init__.py should be a file"

    def test_unit_directory_has_init_file(self):
        """Verify that tests/unit/__init__.py exists."""
        unit_dir = Path(__file__).parent
        init_file = unit_dir / "__init__.py"
        assert init_file.exists(), "tests/unit/__init__.py should exist"
        assert init_file.is_file(), "tests/unit/__init__.py should be a file"

    def test_integration_directory_has_init_file(self):
        """Verify that tests/integration/__init__.py exists."""
        integration_dir = Path(__file__).parent.parent / "integration"
        init_file = integration_dir / "__init__.py"
        assert init_file.exists(), "tests/integration/__init__.py should exist"
        assert init_file.is_file(), "tests/integration/__init__.py should be a file"

    def test_scripts_directory_has_init_file(self):
        """Verify that tests/scripts/__init__.py exists."""
        scripts_dir = Path(__file__).parent.parent / "scripts"
        init_file = scripts_dir / "__init__.py"
        assert init_file.exists(), "tests/scripts/__init__.py should exist"
        assert init_file.is_file(), "tests/scripts/__init__.py should be a file"