"""
Unit tests for T003: Linting and Formatting Configuration.
Verifies that configuration files exist and contain expected settings.
"""
import os
import tomli
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    assert os.path.exists(path), "pyproject.toml must exist for T003"

def test_pyproject_toml_black_config():
    """Verify Black configuration in pyproject.toml."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config
    assert "black" in config["tool"]
    assert config["tool"]["black"]["line-length"] == 88

def test_pyproject_toml_isort_config():
    """Verify Isort configuration in pyproject.toml."""
    path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config
    assert "isort" in config["tool"]
    assert config["tool"]["isort"]["profile"] == "black"

def test_ruff_config_exists():
    """Verify .ruff.toml exists."""
    path = os.path.join(PROJECT_ROOT, ".ruff.toml")
    assert os.path.exists(path), ".ruff.toml must exist for T003"

def test_ruff_config_content():
    """Verify .ruff.toml contains expected linting rules."""
    path = os.path.join(PROJECT_ROOT, ".ruff.toml")
    with open(path, "rb") as f:
        # Ruff config is TOML
        config = tomli.load(f)
    
    assert "lint" in config
    assert "select" in config["lint"]
    # Check for standard error codes
    assert "E" in config["lint"]["select"]
    assert "F" in config["lint"]["select"]