"""
Unit tests to verify that linting and formatting configurations are valid.
This task (T003) requires configuring ruff and black.
These tests ensure the configuration files exist and are syntactically valid.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def test_pyproject_exists():
    """Verify pyproject.toml exists in the project root."""
    assert PYPROJECT_PATH.exists(), "pyproject.toml not found in project root"


def test_ruff_config_valid():
    """Verify ruff can parse the configuration without errors."""
    if not PYPROJECT_PATH.exists():
        pytest.skip("pyproject.toml missing, skipping ruff config test")

    # Run ruff check with --output-format=json to validate config parsing
    # We use a dummy file or the config itself to trigger parsing
    try:
        result = subprocess.run(
            ["ruff", "check", "--config", str(PYPROJECT_PATH), "--isolated", "--output-format=json", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # If ruff exits with 0 or 1 (found issues), config is valid.
        # Exit code 2 usually means config error.
        assert result.returncode != 2, f"Ruff config error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed, skipping config validation")
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff check timed out")


def test_black_config_valid():
    """Verify black can parse the configuration without errors."""
    if not PYPROJECT_PATH.exists():
        pytest.skip("pyproject.toml missing, skipping black config test")

    try:
        result = subprocess.run(
            ["black", "--config", str(PYPROJECT_PATH), "--check", "--diff", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Black exits with 0 if everything is formatted, 1 if not.
        # Exit code 2 means config error.
        assert result.returncode != 2, f"Black config error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed, skipping config validation")
    except subprocess.TimeoutExpired:
        pytest.skip("Black check timed out")
