"""
Unit tests to verify that linting and formatting configurations are present and valid.
"""
import os
import subprocess
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILES = [
    PROJECT_ROOT / "pyproject.toml",
    PROJECT_ROOT / ".flake8",
]

class TestLintingConfiguration:
    """Tests for linting configuration files."""

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists."""
        assert (PROJECT_ROOT / "pyproject.toml").exists(), "pyproject.toml must exist"

    def test_flake8_config_exists(self):
        """Test that .flake8 exists."""
        assert (PROJECT_ROOT / ".flake8").exists(), ".flake8 must exist"

    def test_pyproject_contains_black(self):
        """Test that pyproject.toml contains Black configuration."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "line-length" in content, "pyproject.toml must specify line-length for Black"

    def test_pyproject_contains_ruff(self):
        """Test that pyproject.toml contains Ruff configuration."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

    def test_flake8_config_valid_syntax(self):
        """Test that .flake8 has valid INI syntax by running flake8 with it."""
        flake8_path = PROJECT_ROOT / ".flake8"
        if not flake8_path.exists():
            pytest.skip(".flake8 file not found")

        # Run flake8 with the config file to check for syntax errors
        result = subprocess.run(
            ["flake8", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip("flake8 not installed in test environment")

        # Check if the config file can be read by flake8 without crashing
        result = subprocess.run(
            ["flake8", "--config=.flake8", "--max-line-length=88", "--select=E9,F63,F7,F82", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        # We don't care about lint errors, just that the config parsed correctly
        # If the config is invalid, flake8 usually exits with code 2 or 4 with a specific error
        assert result.returncode in [0, 1], f"flake8 config validation failed: {result.stderr}"

    def test_requirements_includes_linting_tools(self):
        """Test that requirements.txt (or pyproject dependencies) includes linting tools."""
        # Check pyproject.toml dependencies
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "ruff" in content, "ruff must be listed in dependencies"
        assert "black" in content, "black must be listed in dependencies"

    def test_setup_linting_script_exists(self):
        """Test that the setup_linting.py script exists."""
        script_path = PROJECT_ROOT / "code" / "setup_linting.py"
        assert script_path.exists(), "code/setup_linting.py must exist"

    def test_setup_linting_script_executable(self):
        """Test that setup_linting.py can be executed without import errors."""
        script_path = PROJECT_ROOT / "code" / "setup_linting.py"
        if not script_path.exists():
            pytest.skip("setup_linting.py not found")

        result = subprocess.run(
            ["python", str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        # We expect it to run, even if tools aren't installed (it handles that)
        # The main check is that it doesn't crash with ImportError
        assert "ImportError" not in result.stderr, f"Script failed with ImportError: {result.stderr}"
