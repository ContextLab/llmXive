"""
Unit tests for linting and formatting configuration (T003).
Verifies that ruff and black are installed and configured correctly.
"""
import subprocess
import sys
from pathlib import Path

import pytest


class TestLintConfig:
    """Tests for linting tool configuration."""

    def test_ruff_installed(self):
        """Verify ruff is installed and returns a version string."""
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Ruff not found: {result.stderr}"
        assert "ruff" in result.stdout.lower()

    def test_black_installed(self):
        """Verify black is installed and returns a version string."""
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Black not found: {result.stderr}"
        assert "black" in result.stdout.lower()

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in project root."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_toml.exists(), f"pyproject.toml not found at {pyproject_path}"

    def test_black_config_present(self):
        """Verify black configuration exists in pyproject.toml."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

    def test_ruff_config_present(self):
        """Verify ruff configuration exists in pyproject.toml."""
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration missing from pyproject.toml"