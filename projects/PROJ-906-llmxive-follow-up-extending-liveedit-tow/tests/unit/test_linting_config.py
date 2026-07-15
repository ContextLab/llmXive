"""
Unit tests to verify that linting and formatting configurations are valid.
These tests ensure that ruff and black configurations are syntactically correct
and can be loaded by the respective tools.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_ruff_config_valid():
    """Test that ruff.toml exists and is valid."""
    ruff_config = CODE_DIR / "ruff.toml"
    assert ruff_config.exists(), f"ruff.toml not found at {ruff_config}"
    
    # Run ruff check with the config to ensure it's valid
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(ruff_config), "--isolated", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    # We expect exit code 0 (success) or 1 (linting issues found), but not 2 (config error)
    assert result.returncode != 2, f"Ruff config error: {result.stderr}"

def test_black_config_valid():
    """Test that black configuration in pyproject.toml is valid."""
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml not found at {pyproject}"
    
    # Run black --check with the config to ensure it's valid
    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(pyproject), "--check", "--diff", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    # We expect exit code 0 (success) or 1 (formatting issues found), but not 2 (config error)
    assert result.returncode != 2, f"Black config error: {result.stderr}"

def test_ruff_format_check():
    """Test that ruff can run format check."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    # Exit code 0: formatted correctly, 1: formatting needed, 2: error
    assert result.returncode != 2, f"Ruff format check error: {result.stderr}"

def test_black_format_check():
    """Test that black can run format check."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    # Exit code 0: formatted correctly, 1: formatting needed, 2: error
    assert result.returncode != 2, f"Black check error: {result.stderr}"