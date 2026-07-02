"""Tests for linting configuration files."""
import os
import tomli
import pytest

def test_flake8_exists():
    """Verify .flake8 file exists at project root."""
    assert os.path.exists(".flake8"), ".flake8 file not found at project root"

def test_flake8_config():
    """Verify .flake8 contains required settings."""
    with open(".flake8", "r") as f:
        content = f.read()
    
    assert "max-line-length = 100" in content, "max-line-length must be 100"
    assert "exclude = venv" in content or "exclude=venv" in content, "exclude must include venv"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml file not found at project root"

def test_pyproject_black_config():
    """Verify pyproject.toml contains Black configuration."""
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "Missing [tool] section"
    assert "black" in config["tool"], "Missing [tool.black] section"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing line-length in black config"
    assert black_config["line-length"] == 100, "Black line-length must be 100"