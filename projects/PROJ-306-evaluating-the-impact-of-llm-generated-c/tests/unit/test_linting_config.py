"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import toml
from pathlib import Path

def test_ruff_config_exists():
    """Test that .ruff.toml exists in code/ directory."""
    path = Path("code/.ruff.toml")
    assert path.exists(), f"{path} does not exist"

def test_ruff_config_valid():
    """Test that .ruff.toml is a valid TOML file."""
    path = Path("code/.ruff.toml")
    try:
        with open(path, "r") as f:
            config = toml.load(f)
        assert "lint" in config, "Missing 'lint' section in .ruff.toml"
        assert "select" in config["lint"], "Missing 'select' in lint section"
    except Exception as e:
        assert False, f"Failed to parse .ruff.toml: {e}"

def test_black_config_exists():
    """Test that .black.toml exists in code/ directory."""
    path = Path("code/.black.toml")
    assert path.exists(), f"{path} does not exist"

def test_black_config_valid():
    """Test that .black.toml is a valid TOML file."""
    path = Path("code/.black.toml")
    try:
        with open(path, "r") as f:
            config = toml.load(f)
        assert "tool" in config, "Missing 'tool' section in .black.toml"
        assert "black" in config["tool"], "Missing 'black' section in tool"
        assert config["tool"]["black"]["line-length"] == 88, "Incorrect line-length"
    except Exception as e:
        assert False, f"Failed to parse .black.toml: {e}"