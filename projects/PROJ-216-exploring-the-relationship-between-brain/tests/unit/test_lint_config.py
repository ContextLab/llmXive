"""
Unit tests to verify that linting and formatting configurations are present and valid.
"""
import os
import toml
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists at the project root."""
    config_path = ROOT_DIR / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml must exist at project root"

def test_black_config_present():
    """Test that Black configuration is present in pyproject.toml."""
    config_path = ROOT_DIR / "pyproject.toml"
    with open(config_path) as f:
        config = toml.load(f)
    
    assert "tool" in config
    assert "black" in config["tool"]
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Black line-length must be configured"
    assert black_config["line-length"] == 88, "Line length should match standard (88)"
    assert "target-version" in black_config
    assert "py311" in black_config["target-version"]

def test_ruff_config_present():
    """Test that Ruff configuration is present in pyproject.toml."""
    config_path = ROOT_DIR / "pyproject.toml"
    with open(config_path) as f:
        config = toml.load(f)
    
    assert "tool" in config
    assert "ruff" in config["tool"]
    
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config
    assert "target-version" in ruff_config

def test_ruff_lint_rules_selected():
    """Test that basic lint rules are selected in Ruff config."""
    config_path = ROOT_DIR / "pyproject.toml"
    with open(config_path) as f:
        config = toml.load(f)
    
    ruff_lint = config["tool"]["ruff"]["lint"]
    assert "select" in ruff_lint
    # Ensure E, F, W are selected (standard errors)
    selected = ruff_lint["select"]
    assert "E" in selected
    assert "F" in selected
    assert "W" in selected

def test_pytest_config_present():
    """Test that pytest configuration is present."""
    config_path = ROOT_DIR / "pyproject.toml"
    with open(config_path) as f:
        config = toml.load(f)
    
    assert "tool" in config
    assert "pytest" in config["tool"]
    assert "ini_options" in config["tool"]["pytest"]
    
    pytest_opts = config["tool"]["pytest"]["ini_options"]
    assert "testpaths" in pytest_opts
    assert "code" in pytest_opts.get("pythonpath", [])