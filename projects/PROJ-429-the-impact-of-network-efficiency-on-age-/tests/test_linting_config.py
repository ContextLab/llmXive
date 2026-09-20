"""
Test suite to verify that linting and formatting configurations are valid.
These tests ensure that the project's static analysis tools (Ruff, Black, Flake8)
can parse their configuration files without error.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


def test_ruff_config_valid():
    """Verify that .ruff.toml exists and is valid by running ruff check."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_path.exists(), "Ruff configuration file (.ruff.toml) not found"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--config", str(ruff_path), "."],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        # We expect ruff to run successfully (exit code 0 or 1 if issues found).
        # Exit code 2 or 5 indicates a configuration error.
        assert result.returncode not in (2, 5), f"Ruff config error: {result.stderr}"
    except FileNotFoundError:
        # If ruff is not installed, we skip the execution check but assert the file exists
        pytest.skip("Ruff not installed, skipping execution check")


def test_black_config_valid():
    """Verify that pyproject.toml contains valid Black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration section missing from pyproject.toml"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", "--config", str(pyproject_path), "."],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        # Exit code 0: clean, 1: would reformat, 2: config error
        assert result.returncode not in (2,), f"Black config error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed, skipping execution check")


def test_flake8_config_valid():
    """Verify that .flake8 exists and is valid."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), "Flake8 configuration file (.flake8) not found"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--config", str(flake8_path), "--version"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0, f"Flake8 config error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Flake8 not installed, skipping execution check")


def test_ruff_format_compatibility():
    """Ensure Ruff's format settings align with project needs."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    content = ruff_path.read_text()
    assert "quote-style" in content, "Ruff quote-style not configured"
    assert "indent-style" in content, "Ruff indent-style not configured"
