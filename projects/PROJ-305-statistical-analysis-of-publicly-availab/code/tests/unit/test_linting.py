"""
Unit tests to verify that linting and formatting configurations are valid.
These tests ensure that the project's tooling (ruff, black, flake8) is correctly configured.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestLintingConfig:
    """Tests for linting configuration validity."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_ruff_config_exists(self, project_root):
        """Test that .ruff.toml configuration file exists."""
        config_path = project_root / ".ruff.toml"
        assert config_path.exists(), ".ruff.toml configuration file is missing"

    def test_flake8_config_exists(self, project_root):
        """Test that .flake8 configuration file exists."""
        config_path = project_root / ".flake8"
        assert config_path.exists(), ".flake8 configuration file is missing"

    def test_pyproject_black_config(self, project_root):
        """Test that pyproject.toml contains Black configuration."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml is missing"

        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

    def test_ruff_check_syntax(self, project_root):
        """Test that ruff can check syntax without crashing."""
        # Create a temporary valid Python file to test ruff
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    print('world')\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", temp_file],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            # Ruff should exit with 0 if no errors, or 1 if linting issues found
            # We just want to ensure it doesn't crash (exit code 2 or signal)
            assert result.returncode in [0, 1], f"Ruff crashed: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_black_check_syntax(self, project_root):
        """Test that black can check syntax without crashing."""
        # Create a temporary valid Python file to test black
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    print('world')\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", temp_file],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            # Black exits with 0 if formatted correctly, 1 if not
            # We just want to ensure it doesn't crash
            assert result.returncode in [0, 1], f"Black crashed: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_flake8_check_syntax(self, project_root):
        """Test that flake8 can check syntax without crashing."""
        # Create a temporary valid Python file to test flake8
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    print('world')\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", temp_file],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            # Flake8 exits with 0 if no errors, 1 if errors found
            # We just want to ensure it doesn't crash
            assert result.returncode in [0, 1], f"Flake8 crashed: {result.stderr}"
        finally:
            os.unlink(temp_file)