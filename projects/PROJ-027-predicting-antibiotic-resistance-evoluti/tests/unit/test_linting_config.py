"""
Unit tests to verify that linting and formatting configurations are valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"

class TestLintingConfig:
    """Tests for linting configuration files."""

    def test_ruff_config_exists(self):
        """Verify ruff.toml exists in project root."""
        ruff_config = PROJECT_ROOT / "ruff.toml"
        assert ruff_config.exists(), "ruff.toml should exist in project root"

    def test_ruff_config_valid(self):
        """Verify ruff can parse the configuration."""
        ruff_config = PROJECT_ROOT / "ruff.toml"
        if not ruff_config.exists():
            pytest.skip("ruff.toml not found")

        try:
            result = subprocess.run(
                ["ruff", "check", "--config", str(ruff_config), "--no-cache", "."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Ruff returns 0 if no errors, or 1 if linting errors found.
            # We only care that it doesn't crash with a config error.
            assert "Failed to parse" not in result.stderr, f"Invalid ruff config: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("ruff not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("ruff check timed out")

    def test_black_config_exists(self):
        """Verify pyproject.toml exists in project root."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml should exist in project root"

    def test_black_config_valid(self):
        """Verify black can parse the configuration."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("pyproject.toml not found")

        try:
            result = subprocess.run(
                ["black", "--config", str(pyproject), "--check", "--diff", "."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Black returns 0 if formatted correctly, 1 if not.
            # We only care that it doesn't crash with a config error.
            assert "Error:" not in result.stderr or "config" not in result.stderr.lower(), \
                f"Invalid black config: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("black not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("black check timed out")

    def test_ruff_can_run_on_code_dir(self):
        """Verify ruff can run on the code directory."""
        ruff_config = PROJECT_ROOT / "ruff.toml"
        if not ruff_config.exists():
            pytest.skip("ruff.toml not found")

        try:
            result = subprocess.run(
                ["ruff", "check", str(CODE_ROOT)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )
            # Just check it runs without crashing
            assert "Failed to parse" not in result.stderr
        except FileNotFoundError:
            pytest.skip("ruff not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("ruff check on code dir timed out")

    def test_black_can_run_on_code_dir(self):
        """Verify black can run on the code directory."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("pyproject.toml not found")

        try:
            result = subprocess.run(
                ["black", "--config", str(pyproject), "--check", str(CODE_ROOT)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )
            # Just check it runs without crashing
            assert "Error:" not in result.stderr or "config" not in result.stderr.lower()
        except FileNotFoundError:
            pytest.skip("black not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("black check on code dir timed out")