"""
Unit tests for linting configuration validation.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.setup_linting import ensure_tool_installed, validate_config


class TestLintingSetup:
    def test_pyproject_exists(self):
        """Test that pyproject.toml exists in the project root."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist"

    def test_validate_config_returns_true(self):
        """Test that validate_config returns True when config exists."""
        # This relies on the file existing, which is checked above
        assert validate_config() is True

    def test_ruff_installed(self):
        """Test that ruff is installed."""
        assert ensure_tool_installed("ruff") is True

    def test_black_installed(self):
        """Test that black is installed."""
        assert ensure_tool_installed("black") is True

    def test_ruff_check_executes(self):
        """Test that ruff check command executes without import errors."""
        result = subprocess.run(
            ["ruff", "check", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stderr}"

    def test_black_check_executes(self):
        """Test that black check command executes without import errors."""
        result = subprocess.run(
            ["black", "--check", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Black check failed: {result.stderr}"