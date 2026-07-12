"""
Tests to verify linting and formatting configuration exists and is valid.
These tests ensure that the project is properly configured for code quality.
"""
import os
import toml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "code", "pyproject.toml")
RUFF_PATH = os.path.join(PROJECT_ROOT, "code", ".ruff.toml")

def test_pyproject_exists():
    """Test that pyproject.toml exists in the code directory."""
    assert os.path.exists(PYPROJECT_PATH), f"pyproject.toml not found at {PYPROJECT_PATH}"

def test_ruff_config_exists():
    """Test that .ruff.toml exists in the code directory."""
    assert os.path.exists(RUFF_PATH), f".ruff.toml not found at {RUFF_PATH}"

def test_pyproject_has_black_config():
    """Test that pyproject.toml contains black configuration."""
    with open(PYPROJECT_PATH, "r") as f:
        config = toml.load(f)

    assert "tool" in config
    assert "black" in config["tool"]
    assert config["tool"]["black"]["line-length"] == 88

def test_pyproject_has_pytest_config():
    """Test that pyproject.toml contains pytest configuration."""
    with open(PYPROJECT_PATH, "r") as f:
        config = toml.load(f)

    assert "tool" in config
    assert "pytest" in config["tool"]
    assert "ini_options" in config["tool"]["pytest"]

def test_ruff_config_has_valid_syntax():
    """Test that .ruff.toml can be parsed as valid TOML."""
    # This will raise an exception if the file is invalid
    with open(RUFF_PATH, "r") as f:
        config = toml.load(f)

    assert "lint" in config

def test_black_excludes_data_directory():
    """Test that black is configured to exclude data directories."""
    with open(PYPROJECT_PATH, "r") as f:
        config = toml.load(f)

    black_config = config["tool"]["black"]
    assert "exclude" in black_config
    assert "data" in black_config["exclude"]