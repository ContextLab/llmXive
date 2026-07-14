"""
Tests for the linting and formatting setup.
"""
import os
from pathlib import Path

def test_ruff_config_exists():
    """Test that ruff.toml exists in the config directory."""
    config_path = Path("code/config/ruff.toml")
    assert config_path.exists(), f"ruff.toml not found at {config_path}"

def test_black_config_exists():
    """Test that black.toml exists in the config directory."""
    config_path = Path("code/config/black.toml")
    assert config_path.exists(), f"black.toml not found at {config_path}"

def test_ruff_config_valid_syntax():
    """Test that ruff.toml has valid TOML syntax."""
    try:
        import tomli
    except ImportError:
        import tomllib as tomli

    config_path = Path("code/config/ruff.toml")
    with open(config_path, "rb") as f:
        tomli.load(f)

def test_black_config_valid_syntax():
    """Test that black.toml has valid TOML syntax."""
    try:
        import tomli
    except ImportError:
        import tomllib as tomli

    config_path = Path("code/config/black.toml")
    with open(config_path, "rb") as f:
        tomli.load(f)