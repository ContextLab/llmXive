"""
Unit tests to verify that linting and formatting configurations are correctly set up.
These tests ensure that black and ruff are available and configured as expected.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"


def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists in the project root."""
    assert PYPROJECT_TOML.exists(), "pyproject.toml not found in project root"


def test_black_section_exists():
    """Verify that the [tool.black] section exists in pyproject.toml."""
    content = PYPROJECT_TOML.read_text()
    assert "[tool.black]" in content, "[tool.black] section missing from pyproject.toml"
    assert "line-length = 88" in content, "Black line-length configuration missing"


def test_ruff_section_exists():
    """Verify that the [tool.ruff] section exists in pyproject.toml."""
    content = PYPROJECT_TOML.read_text()
    assert "[tool.ruff]" in content, "[tool.ruff] section missing from pyproject.toml"
    assert "line-length = 88" in content, "Ruff line-length configuration missing"


def test_black_format_check_available():
    """Verify that black is installed and can run a format check."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Black not installed or not working: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")


def test_ruff_check_available():
    """Verify that ruff is installed and can run a lint check."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Ruff not installed or not working: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")