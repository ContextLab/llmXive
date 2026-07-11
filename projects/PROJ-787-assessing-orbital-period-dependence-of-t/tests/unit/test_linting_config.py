"""
Unit tests to verify linting configuration is present and valid.
These tests check that the required configuration files exist.
"""
import os
import toml
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def test_flake8_config_exists(project_root):
    """Test that .flake8 configuration file exists."""
    flake8_path = project_root / "code" / ".flake8"
    assert flake8_path.exists(), "Missing .flake8 configuration file"


def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml exists with black and pytest config."""
    pyproject_path = project_root / "code" / "pyproject.toml"
    assert pyproject_path.exists(), "Missing pyproject.toml configuration file"

    with open(pyproject_path) as f:
        config = toml.load(f)

    # Check for black configuration
    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] configuration"
    assert "line-length" in config["tool"]["black"], "Missing line-length in black config"

    # Check for pytest configuration
    assert "pytest" in config["tool"], "Missing [tool.pytest] configuration"
    assert "testpaths" in config["tool"]["pytest"], "Missing testpaths in pytest config"


def test_flake8_config_valid(project_root):
    """Test that .flake8 configuration is valid."""
    flake8_path = project_root / "code" / ".flake8"
    assert flake8_path.exists()

    with open(flake8_path) as f:
        content = f.read()

    # Check for required sections
    assert "[flake8]" in content, "Missing [flake8] section"
    assert "max-line-length" in content, "Missing max-line-length setting"


def test_black_config_valid(project_root):
    """Test that black configuration in pyproject.toml is valid."""
    pyproject_path = project_root / "code" / "pyproject.toml"
    with open(pyproject_path) as f:
        config = toml.load(f)

    black_config = config["tool"]["black"]
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "py39" in black_config["target-version"], "Should target Python 3.9+"