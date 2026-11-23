"""
Contract test to verify that linting and formatting configurations are present and valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent.parent
RUFF_CONFIG = ROOT_DIR / ".ruff.toml"
PYPROJECT_CONFIG = ROOT_DIR / "pyproject.toml"


def test_ruff_config_exists():
    """Test that .ruff.toml configuration file exists."""
    assert RUFF_CONFIG.exists(), f"Ruff config file not found at {RUFF_CONFIG}"


def test_pyproject_config_exists():
    """Test that pyproject.toml configuration file exists."""
    assert PYPROJECT_CONFIG.exists(), f"Pyproject config file not found at {PYPROJECT_CONFIG}"


def test_ruff_can_check_code():
    """Test that ruff can successfully check the codebase (even if issues are found)."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(ROOT_DIR)],
        capture_output=True,
        text=True
    )
    # We expect ruff to run without crashing. Exit code 1 is fine if issues are found.
    assert result.returncode in (0, 1), f"Ruff check crashed: {result.stderr}"


def test_black_can_check_code():
    """Test that black can successfully check the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(ROOT_DIR)],
        capture_output=True,
        text=True
    )
    # We expect black to run without crashing. Exit code 1 is fine if formatting is needed.
    assert result.returncode in (0, 1), f"Black check crashed: {result.stderr}"