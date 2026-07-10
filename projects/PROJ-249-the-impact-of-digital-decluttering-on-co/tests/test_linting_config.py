"""
Contract tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import tomli
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent / "code"


def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), ".flake8 configuration file is missing"
    assert flake8_path.stat().st_size > 0, ".flake8 file is empty"


def test_pylint_config_exists():
    """Verify .pylintrc configuration file exists."""
    pylint_path = PROJECT_ROOT / ".pylintrc"
    assert pylint_path.exists(), ".pylintrc configuration file is missing"
    assert pylint_path.stat().st_size > 0, ".pylintrc file is empty"


def test_pyproject_black_config():
    """Verify black configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml is missing"

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "black" in config["tool"], "No [tool.black] section found"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Black line-length not configured"
    assert black_config["line-length"] == 120, f"Expected line-length 120, got {black_config['line-length']}"


def test_pyproject_pytest_config():
    """Verify pytest configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml is missing"

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "pytest.ini_options" in config["tool"], "No [tool.pytest.ini_options] found"

    pytest_config = config["tool"]["pytest"]["ini_options"]
    assert "addopts" in pytest_config, "Pytest addopts not configured"
    assert "testpaths" in pytest_config, "Pytest testpaths not configured"