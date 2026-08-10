"""
Unit tests to verify linting and formatting configuration setup.
These tests ensure that the required configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

# Helper to find project root
def get_project_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return current.parent

PROJECT_ROOT = get_project_root()

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in project root."""
    assert (PROJECT_ROOT / "pyproject.toml").exists(), "pyproject.toml not found"

def test_pyproject_toml_has_ruff_config():
    """Test that pyproject.toml contains ruff configuration."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "No 'tool' section in pyproject.toml"
    assert "ruff" in config["tool"], "No 'ruff' configuration found"
    assert config["tool"]["ruff"].get("line-length") == 88, "Ruff line-length should be 88"
    assert "select" in config["tool"]["ruff"], "Ruff 'select' list is missing"

def test_pyproject_toml_has_black_config():
    """Test that pyproject.toml contains black configuration."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "No 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "No 'black' configuration found"
    assert config["tool"]["black"].get("line-length") == 88, "Black line-length should be 88"

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    assert (PROJECT_ROOT / ".flake8").exists(), ".flake8 file not found"

def test_flake8_config_valid():
    """Test that .flake8 file has valid configuration."""
    config_path = PROJECT_ROOT / ".flake8"
    with open(config_path, "r") as f:
        content = f.read()

    assert "[flake8]" in content, "Missing [flake8] section in .flake8"
    assert "max-line-length" in content, "Missing max-line-length in .flake8"

def test_dev_dependencies_included():
    """Test that dev dependencies (ruff, black, isort) are in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "r") as f:
        config = toml.load(f)

    dev_deps = config.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    dep_names = [d.split(">=")[0].split("<")[0] for d in dev_deps]

    assert "ruff" in dep_names, "ruff not in dev dependencies"
    assert "black" in dep_names, "black not in dev dependencies"
    assert "isort" in dep_names, "isort not in dev dependencies"
