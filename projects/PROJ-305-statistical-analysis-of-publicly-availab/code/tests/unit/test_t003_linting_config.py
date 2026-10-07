"""
Test for T003: Linting and Formatting Configuration.
Verifies that ruff and black are correctly configured in pyproject.toml.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest
import tomli

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_pyproject_toml_exists():
    """Ensure pyproject.toml exists at the project root."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml must exist in the project root"

def test_ruff_configuration_present():
    """Verify ruff configuration exists in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "tool section must exist"
    assert "ruff" in config["tool"], "ruff configuration must exist under [tool.ruff]"

    ruff_config = config["tool"]["ruff"]
    assert "target-version" in ruff_config, "ruff target-version must be defined"
    assert "line-length" in ruff_config, "ruff line-length must be defined"

def test_black_configuration_present():
    """Verify black configuration exists in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "tool section must exist"
    assert "black" in config["tool"], "black configuration must exist under [tool.black]"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "black line-length must be defined"
    assert "target-version" in black_config, "black target-version must be defined"

def test_ruff_check_syntax():
    """Run ruff check on the codebase to ensure configuration is valid."""
    # Only check the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/src", "--output-format=json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We expect this to run without a configuration error (exit code 0 or 1 is fine, 2 is config error)
    # Exit code 2 usually indicates a configuration error or internal error
    assert result.returncode != 2, f"Ruff configuration error: {result.stderr}"

def test_black_check_syntax():
    """Run black --check on the codebase to ensure configuration is valid."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "code/src"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # Exit code 0: all good, 1: would reformat, 123: configuration error
    assert result.returncode != 123, f"Black configuration error: {result.stderr}"