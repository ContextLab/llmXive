"""
Tests for linting and formatting configuration.
These tests verify that the configuration files exist and are valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Test suite for linting setup."""

    def test_ruff_toml_exists(self):
        """Verify ruff.toml configuration file exists."""
        assert Path("ruff.toml").exists(), "ruff.toml must exist in project root"

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists."""
        assert Path("pyproject.toml").exists(), "pyproject.toml must exist in project root"

    def test_pyproject_has_black_config(self):
        """Verify pyproject.toml contains black configuration."""
        pyproject_path = Path("pyproject.toml")
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

    def test_pyproject_has_ruff_config(self):
        """Verify pyproject.toml contains ruff configuration."""
        pyproject_path = Path("pyproject.toml")
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

    def test_ruff_check_runs(self):
        """Verify ruff check command runs without error on the codebase."""
        # Run ruff check on the code directory
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/"],
            capture_output=True,
            text=True
        )
        # We expect exit code 0 (success) or 1 (found issues, but command ran)
        # The command itself must not fail (e.g., command not found)
        assert result.returncode in (0, 1), f"Ruff check failed to run: {result.stderr}"

    def test_black_check_runs(self):
        """Verify black check command runs without error on the codebase."""
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "code/"],
            capture_output=True,
            text=True
        )
        # Exit code 0 (ok) or 1 (would reformat) is acceptable for "command runs"
        assert result.returncode in (0, 1), f"Black check failed to run: {result.stderr}"
