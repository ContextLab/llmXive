"""
Tests to verify that linting (ruff) and formatting (black) configurations are present and valid.
"""
import os
import toml
import pytest
from pathlib import Path

# Assume tests are in code/tests/, project root is code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_ruff_config_exists():
    """Verify that ruff configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "ruff" in config["tool"], "No [tool.ruff] section in pyproject.toml"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "black" in config["tool"], "No [tool.black] section in pyproject.toml"

def test_black_config_valid():
    """Verify that black configuration has required fields."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "black config missing 'line-length'"
    assert isinstance(black_config["line-length"], int), "black 'line-length' must be an integer"

def test_ruff_config_valid():
    """Verify that ruff configuration has required fields."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "ruff config missing 'line-length'"
    assert isinstance(ruff_config["line-length"], int), "ruff 'line-length' must be an integer"