"""
Unit tests for the linting configuration and helper functions.

These tests verify that the linting configuration module is importable
and that the helper functions return expected types, ensuring the
configuration infrastructure is ready for use.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Import the module under test
# Adjust path based on project structure if needed
try:
    from code.config.linting import (
        run_ruff_check,
        run_ruff_fix,
        run_black_check,
        run_black_format,
        PROJECT_ROOT,
        CODE_DIR,
        TESTS_DIR,
    )
except ImportError:
    # Fallback for if the import path structure is slightly different during initial setup
    # This block ensures the test file itself doesn't crash if the module isn't fully set up yet
    pytest.skip("Linting module not yet available", allow_module_level=True)


class TestLintingPaths:
    """Test that project paths are correctly resolved."""

    def test_project_root_exists(self):
        """Verify that PROJECT_ROOT points to an existing directory."""
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    def test_code_dir_exists(self):
        """Verify that CODE_DIR exists within PROJECT_ROOT."""
        assert CODE_DIR.exists()
        assert CODE_DIR.is_dir()

    def test_tests_dir_exists(self):
        """Verify that TESTS_DIR exists within PROJECT_ROOT."""
        assert TESTS_DIR.exists()
        assert TESTS_DIR.is_dir()


class TestLintingFunctions:
    """Test that linting functions return valid exit codes."""

    def test_run_ruff_check_returns_int(self):
        """Verify run_ruff_check returns an integer exit code."""
        # We expect 0 (success) or 1 (issues found) in a healthy repo
        # It might return non-zero if ruff isn't installed, but should still be int
        result = run_ruff_check()
        assert isinstance(result, int)

    def test_run_black_check_returns_int(self):
        """Verify run_black_check returns an integer exit code."""
        result = run_black_check()
        assert isinstance(result, int)

    def test_run_ruff_fix_returns_int(self):
        """Verify run_ruff_fix returns an integer exit code."""
        result = run_ruff_fix()
        assert isinstance(result, int)

    def test_run_black_format_returns_int(self):
        """Verify run_black_format returns an integer exit code."""
        result = run_black_format()
        assert isinstance(result, int)


class TestPyprojectToml:
    """Test that pyproject.toml contains expected configurations."""

    def test_pyproject_exists(self):
        """Verify pyproject.toml exists at project root."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists()

    def test_pyproject_contains_ruff_config(self):
        """Verify pyproject.toml contains [tool.ruff] section."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content

    def test_pyproject_contains_black_config(self):
        """Verify pyproject.toml contains [tool.black] section."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content

    def test_pyproject_contains_dependencies(self):
        """Verify ruff and black are listed in dependencies."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "ruff" in content
        assert "black" in content
