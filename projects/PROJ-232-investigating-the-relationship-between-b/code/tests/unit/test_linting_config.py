"""
Unit tests to verify linting and formatting configuration files exist and are valid.
These tests ensure T003 (Configure linting and formatting tools) is complete.
"""
import os
import tomllib
import pytest
from pathlib import Path

# Base directory for the project (assuming code/ is the root for config)
# Adjust based on actual project root if running from different context
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def test_black_config_exists():
    """Verify pyproject.toml exists and contains [tool.black] section."""
    config_path = BASE_DIR / "pyproject.toml"
    assert config_path.exists(), f"pyproject.toml not found at {config_path}"
    
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    assert "tool" in config, "Missing 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] configuration"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing line-length in black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"

def test_ruff_config_exists():
    """Verify .ruff.toml exists and contains valid configuration."""
    config_path = BASE_DIR / ".ruff.toml"
    assert config_path.exists(), f".ruff.toml not found at {config_path}"
    
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    assert "lint" in config, "Missing [lint] section in .ruff.toml"
    assert "select" in config["lint"], "Missing 'select' in [lint] section"
    assert "E" in config["lint"]["select"], "Should include pycodestyle errors"
    assert "F" in config["lint"]["select"], "Should include pyflake"

def test_requirements_include_linting_tools():
    """Verify requirements.txt includes black and ruff."""
    req_path = BASE_DIR / "requirements.txt"
    assert req_path.exists(), f"requirements.txt not found at {req_path}"
    
    with open(req_path, "r") as f:
        content = f.read().lower()
    
    assert "black" in content, "Missing 'black' in requirements.txt"
    assert "ruff" in content, "Missing 'ruff' in requirements.txt"
    assert "flake8" in content, "Missing 'flake8' in requirements.txt"

def test_config_syntax_valid():
    """Verify that the configuration files are syntactically valid TOML."""
    # Test pyproject.toml
    pyproject_path = BASE_DIR / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        try:
            tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML in pyproject.toml: {e}")
    
    # Test .ruff.toml
    ruff_path = BASE_DIR / ".ruff.toml"
    with open(ruff_path, "rb") as f:
        try:
            tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

def test_file_locations_correct():
    """Verify configuration files are in the correct project root."""
    assert (BASE_DIR / "pyproject.toml").exists(), "pyproject.toml must be in project root"
    assert (BASE_DIR / ".ruff.toml").exists(), ".ruff.toml must be in project root"
    assert (BASE_DIR / "requirements.txt").exists(), "requirements.txt must be in project root"