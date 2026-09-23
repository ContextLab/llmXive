"""
Unit tests for linting and formatting configuration.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest


def test_ruff_config_exists():
    """Test that ruff.toml configuration file exists."""
    assert Path("ruff.toml").exists(), "ruff.toml configuration file should exist"


def test_pyproject_black_config():
    """Test that pyproject.toml contains black configuration."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml should exist"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml should contain [tool.black] section"


def test_ruff_command_available():
    """Test that ruff command is available in the environment."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"ruff command failed: {result.stderr}"
    assert "ruff" in result.stdout.lower(), "ruff version output should contain 'ruff'"


def test_black_command_available():
    """Test that black command is available in the environment."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"black command failed: {result.stderr}"
    assert "black" in result.stdout.lower(), "black version output should contain 'black'"


def test_ruff_check_runs():
    """Test that ruff check command runs without crashing."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        capture_output=True,
        text=True
    )
    # ruff check may return non-zero if there are linting errors, but it should not crash
    assert result.returncode in [0, 1], f"ruff check crashed: {result.stderr}"


def test_black_check_runs():
    """Test that black --check command runs without crashing."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        capture_output=True,
        text=True
    )
    # black --check may return non-zero if files are not formatted, but it should not crash
    assert result.returncode in [0, 1], f"black --check crashed: {result.stderr}"