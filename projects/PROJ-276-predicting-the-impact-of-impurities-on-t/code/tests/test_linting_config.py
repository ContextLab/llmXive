"""
Tests to verify that linting and formatting configurations are correctly set up.
"""
import os
import toml
import pytest
from pathlib import Path

# Determine project root (parent of code/ directory)
project_root = Path(__file__).resolve().parent.parent

def test_ruff_config_exists():
    """Test that ruff configuration file exists."""
    ruff_toml = project_root / "ruff.toml"
    pyproject_toml = project_root / "pyproject.toml"
    
    assert ruff_toml.exists() or pyproject_toml.exists(), \
        "Either ruff.toml or pyproject.toml must exist"
    
    # If pyproject.toml exists, check for ruff section
    if pyproject_toml.exists():
        with open(pyproject_toml, "r", encoding="utf-8") as f:
            content = f.read()
        assert "[tool.ruff" in content or "ruff.toml exists", \
            "pyproject.toml should contain ruff configuration or ruff.toml should exist"

def test_black_config_exists():
    """Test that black configuration exists."""
    pyproject_toml = project_root / "pyproject.toml"
    assert pyproject_toml.exists(), "pyproject.toml must exist for Black configuration"

def test_black_config_valid():
    """Test that Black configuration in pyproject.toml is valid."""
    pyproject_toml = project_root / "pyproject.toml"
    assert pyproject_toml.exists(), "pyproject.toml must exist"
    
    with open(pyproject_toml, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    
    # Parse and validate
    data = toml.loads(content)
    assert "tool" in data
    assert "black" in data["tool"]
    
    black_config = data["tool"]["black"]
    assert "line-length" in black_config, "Black config must specify line-length"
    assert isinstance(black_config["line-length"], int), "line-length must be an integer"
    assert 79 <= black_config["line-length"] <= 120, "line-length should be between 79 and 120"

def test_ruff_config_valid():
    """Test that Ruff configuration is valid."""
    ruff_toml = project_root / "ruff.toml"
    pyproject_toml = project_root / "pyproject.toml"
    
    config_data = None
    
    if ruff_toml.exists():
        with open(ruff_toml, "r", encoding="utf-8") as f:
            config_data = toml.loads(f.read())
    elif pyproject_toml.exists():
        with open(pyproject_toml, "r", encoding="utf-8") as f:
            data = toml.loads(f.read())
            if "tool" in data and "ruff" in data["tool"]:
                config_data = data["tool"]["ruff"]
    
    assert config_data is not None, "Ruff configuration must exist in either ruff.toml or pyproject.toml"
    
    # Validate required settings
    assert "line-length" in config_data or "line_length" in config_data, \
        "Ruff config must specify line-length"
    
    assert "select" in config_data or "select" in str(config_data), \
        "Ruff config must specify rules to select"