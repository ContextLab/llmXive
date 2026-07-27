"""
Unit tests for linting and formatting setup configuration.
Verifies that ruff and black configurations are valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).parent.parent.parent / "code"

def test_ruff_config_exists():
    """Test that .ruff.toml exists in code directory."""
    config_path = CODE_DIR / ".ruff.toml"
    assert config_path.exists(), f"Ruff config missing: {config_path}"

def test_pyproject_config_exists():
    """Test that pyproject.toml exists in code directory."""
    config_path = CODE_DIR / "pyproject.toml"
    assert config_path.exists(), f"Pyproject.toml missing: {config_path}"

def test_ruff_syntax_check():
    """Test that ruff can parse the configuration without errors."""
    result = subprocess.run(
        ["ruff", "check", "--config", str(CODE_DIR / ".ruff.toml"), str(CODE_DIR)],
        capture_output=True,
        text=True,
    )
    # We expect this to pass (exit code 0) if config is valid,
    # or fail with linting errors (exit code 1) which is also valid config.
    # We only fail if ruff crashes (exit code 2) or config is invalid.
    assert result.returncode != 2, f"Ruff configuration error: {result.stderr}"

def test_black_syntax_check():
    """Test that black can parse the configuration without errors."""
    result = subprocess.run(
        ["black", "--check", "--config", str(CODE_DIR / "pyproject.toml"), "--diff", str(CODE_DIR)],
        capture_output=True,
        text=True,
    )
    # Exit code 0 = all good, 1 = would reformat (valid config), 2 = error
    assert result.returncode != 2, f"Black configuration error: {result.stderr}"

def test_setup_linting_script_exists():
    """Test that setup_linting.py exists."""
    script_path = CODE_DIR / "setup_linting.py"
    assert script_path.exists(), f"Setup script missing: {script_path}"

def test_run_linting_script_exists():
    """Test that 06_run_linting.py exists."""
    script_path = CODE_DIR / "06_run_linting.py"
    assert script_path.exists(), f"Run linting script missing: {script_path}"