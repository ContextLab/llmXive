"""
Unit tests to verify that linting and formatting configurations are valid.
These tests ensure that ruff and black can parse the project configuration
and that the configuration files exist.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILES = [
    PROJECT_ROOT / "pyproject.toml",
    PROJECT_ROOT / ".ruff.toml",
]

class TestLintingConfiguration:
    """Tests for linting configuration validity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we are in the correct project directory."""
        self.original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        yield
        os.chdir(self.original_cwd)

    def test_config_files_exist(self):
        """Verify that configuration files exist in the project root."""
        for config_file in CONFIG_FILES:
            assert config_file.exists(), f"Configuration file {config_file} does not exist."
            assert config_file.stat().st_size > 0, f"Configuration file {config_file} is empty."

    def test_ruff_check_passes(self):
        """Run ruff check on the code directory to ensure no configuration errors."""
        try:
            result = subprocess.run(
                ["ruff", "check", "code"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # We expect ruff to run successfully (exit code 0 or 1 if issues found).
            # Exit code 2 indicates a configuration error or crash.
            assert result.returncode != 2, f"Ruff check failed with configuration error:\n{result.stderr}"
        except FileNotFoundError:
            pytest.skip("Ruff is not installed in the environment.")
        except subprocess.TimeoutExpired:
            pytest.fail("Ruff check timed out.")

    def test_black_check_passes(self):
        """Run black --check on the code directory to ensure formatting config is valid."""
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", "code"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Exit code 0: all good. Exit code 1: files would be reformatted (still valid config).
            # Exit code 2: configuration error.
            assert result.returncode != 2, f"Black check failed with configuration error:\n{result.stderr}"
        except FileNotFoundError:
            pytest.skip("Black is not installed in the environment.")
        except subprocess.TimeoutExpired:
            pytest.fail("Black check timed out.")

    def test_pyproject_toml_valid_syntax(self):
        """Verify that pyproject.toml contains valid TOML syntax."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        config_path = PROJECT_ROOT / "pyproject.toml"
        try:
            with open(config_path, "rb") as f:
                tomllib.load(f)
        except Exception as e:
            pytest.fail(f"pyproject.toml contains invalid TOML syntax: {e}")
