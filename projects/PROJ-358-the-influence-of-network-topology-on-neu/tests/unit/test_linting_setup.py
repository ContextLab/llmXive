"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

# Adjust path if running from root or package
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "code"

def test_ruff_config_exists():
    """Verify .ruff.toml exists."""
    config_path = BASE_DIR / ".ruff.toml"
    assert config_path.exists(), f"Configuration file {config_path} does not exist."

def test_black_config_exists():
    """Verify .black.toml exists."""
    config_path = BASE_DIR / ".black.toml"
    assert config_path.exists(), f"Configuration file {config_path} does not exist."

def test_ruff_config_valid():
    """Verify .ruff.toml is valid TOML and contains expected keys."""
    config_path = BASE_DIR / ".ruff.toml"
    try:
        with open(config_path, "r") as f:
            data = toml.load(f)
        assert "lint" in data, "Missing 'lint' section in ruff config."
        assert "select" in data["lint"], "Missing 'select' key in ruff lint config."
    except Exception as e:
        pytest.fail(f"Invalid ruff config: {e}")

def test_black_config_valid():
    """Verify .black.toml is valid TOML and contains expected keys."""
    config_path = BASE_DIR / ".black.toml"
    try:
        with open(config_path, "r") as f:
            data = toml.load(f)
        # Black uses [tool.black]
        assert "tool" in data, "Missing 'tool' section in black config."
        assert "black" in data["tool"], "Missing 'black' section in black config."
    except Exception as e:
        pytest.fail(f"Invalid black config: {e}")

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    config_path = BASE_DIR / ".pre-commit-config.yaml"
    assert config_path.exists(), f"Configuration file {config_path} does not exist."

def test_setup_linting_script_exists():
    """Verify setup_linting.py exists."""
    script_path = BASE_DIR / "setup_linting.py"
    assert script_path.exists(), f"Setup script {script_path} does not exist."
