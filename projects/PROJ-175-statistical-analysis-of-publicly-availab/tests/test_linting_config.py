"""
Tests to verify that linting and formatting configuration files exist
and are valid (syntax check for TOML/INI).
"""
import os
import toml
import configparser
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_ruff_config_exists():
    """Test that .ruff.toml exists."""
    path = os.path.join(CODE_DIR, ".ruff.toml")
    assert os.path.exists(path), f"Config file {path} does not exist."

def test_ruff_config_valid():
    """Test that .ruff.toml is valid TOML."""
    path = os.path.join(CODE_DIR, ".ruff.toml")
    try:
        with open(path, "r") as f:
            toml.load(f)
    except toml.TomlDecodeError as e:
        pytest.fail(f".ruff.toml is not valid TOML: {e}")

def test_black_config_exists():
    """Test that .black exists (INI format)."""
    path = os.path.join(CODE_DIR, ".black")
    assert os.path.exists(path), f"Config file {path} does not exist."

def test_black_config_valid():
    """Test that .black is valid INI."""
    path = os.path.join(CODE_DIR, ".black")
    config = configparser.ConfigParser()
    try:
        config.read(path)
        assert "tool.black" in config, "Missing [tool.black] section in .black"
    except configparser.Error as e:
        pytest.fail(f".black is not valid INI: {e}")

def test_flake8_config_exists():
    """Test that .flake8 exists."""
    path = os.path.join(CODE_DIR, ".flake8")
    assert os.path.exists(path), f"Config file {path} does not exist."

def test_flake8_config_valid():
    """Test that .flake8 is valid INI."""
    path = os.path.join(CODE_DIR, ".flake8")
    config = configparser.ConfigParser()
    try:
        config.read(path)
        assert "flake8" in config, "Missing [flake8] section in .flake8"
    except configparser.Error as e:
        pytest.fail(f".flake8 is not valid INI: {e}")
