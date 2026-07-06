"""
Tests to verify that the project tooling configuration files exist and are valid.
"""
import os
import tomli
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    path = os.path.join(ROOT_DIR, ".flake8")
    assert os.path.exists(path), f"Missing .flake8 configuration at {path}"

def test_pyproject_black_config():
    """Verify black configuration exists in pyproject.toml."""
    path = os.path.join(ROOT_DIR, "pyproject.toml")
    assert os.path.exists(path), f"Missing pyproject.toml at {path}"
    
    with open(path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config
    assert "black" in config["tool"]
    assert "line-length" in config["tool"]["black"]
    assert config["tool"]["black"]["line-length"] == 88

def test_pyproject_mypy_config():
    """Verify mypy configuration exists in pyproject.toml."""
    path = os.path.join(ROOT_DIR, "pyproject.toml")
    with open(path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config
    assert "mypy" in config["tool"]
    assert config["tool"]["mypy"]["python_version"] == "3.11"
    assert config["tool"]["mypy"]["disallow_untyped_defs"] is True

def test_requirements_includes_dev_tools():
    """Verify requirements.txt includes dev tools."""
    path = os.path.join(ROOT_DIR, "requirements.txt")
    assert os.path.exists(path), f"Missing requirements.txt at {path}"
    
    with open(path, "r") as f:
        content = f.read().lower()
    
    assert "flake8" in content, "flake8 missing from requirements.txt"
    assert "black" in content, "black missing from requirements.txt"
    assert "mypy" in content, "mypy missing from requirements.txt"
    assert "pytest" in content, "pytest missing from requirements.txt"