"""
Tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import tomllib
import pytest

CODE_DIR = os.path.join(os.path.dirname(__file__), "..", "code")

def test_ruff_config_exists():
    """Verify .ruff.toml exists in the code directory."""
    path = os.path.join(CODE_DIR, ".ruff.toml")
    assert os.path.exists(path), f"Configuration file {path} does not exist."

def test_ruff_config_valid():
    """Verify .ruff.toml is valid TOML."""
    path = os.path.join(CODE_DIR, ".ruff.toml")
    with open(path, "rb") as f:
        try:
            config = tomllib.load(f)
            assert "lint" in config, "Missing 'lint' section in .ruff.toml"
        except Exception as e:
            pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

def test_black_config_exists():
    """Verify .black.toml exists in the code directory."""
    path = os.path.join(CODE_DIR, ".black.toml")
    assert os.path.exists(path), f"Configuration file {path} does not exist."

def test_black_config_valid():
    """Verify .black.toml is valid TOML."""
    path = os.path.join(CODE_DIR, ".black.toml")
    with open(path, "rb") as f:
        try:
            config = tomllib.load(f)
            assert "tool" in config, "Missing 'tool' section in .black.toml"
            assert "black" in config["tool"], "Missing 'black' section in .black.toml"
        except Exception as e:
            pytest.fail(f"Invalid TOML in .black.toml: {e}")

def test_setup_script_exists():
    """Verify setup_linting.py exists."""
    path = os.path.join(CODE_DIR, "setup_linting.py")
    assert os.path.exists(path), f"Setup script {path} does not exist."