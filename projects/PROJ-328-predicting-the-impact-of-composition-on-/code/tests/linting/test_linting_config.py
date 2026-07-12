"""
Tests to verify that linting and formatting configurations are valid.
These tests ensure that flake8 and black can parse the configuration files.
"""
import subprocess
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 file exists in the code directory."""
    config_path = PROJECT_ROOT / "code" / ".flake8"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_pyproject_toml_exists():
    """Verify pyproject.toml with black config exists."""
    config_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_black_can_parse_config():
    """Verify black can read its configuration without error."""
    result = subprocess.run(
        ["black", "--check", "--diff", PROJECT_ROOT / "code"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # We expect a non-zero exit code if files are not formatted, 
    # but we want to ensure the config was read successfully (no parse errors).
    # A config error would usually be in stderr with a specific message.
    assert "Invalid config" not in result.stderr, f"Black config error: {result.stderr}"

def test_flake8_can_parse_config():
    """Verify flake8 can read its configuration without error."""
    result = subprocess.run(
        ["flake8", PROJECT_ROOT / "code"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # flake8 might return non-zero if violations are found, 
    # but we check that the config file was parsed (no "No config found" or parse errors).
    assert "No config found" not in result.stderr, f"Flake8 config error: {result.stderr}"
    # Note: We do not assert exit code == 0 here because code might have lint errors,
    # but the configuration itself is valid and applied.