"""
Unit tests for T003: Linting and Formatting Configuration.
Verifies that configuration files exist, are non-empty, and contain expected keys.
"""
import os
import sys
import toml
import pytest
from pathlib import Path

# Add code directory to path for imports if needed, though we mostly check files
CODE_DIR = Path(__file__).parent.parent / "code"

@pytest.fixture
def ruff_config_path():
    return CODE_DIR / ".ruff.toml"

@pytest.fixture
def pyproject_path():
    return CODE_DIR / "pyproject.toml"

@pytest.fixture
def requirements_path():
    return CODE_DIR / "requirements.txt"

def test_ruff_config_exists(ruff_config_path):
    """Verify .ruff.toml exists."""
    assert ruff_config_path.exists(), "ruff config file .ruff.toml must exist"

def test_ruff_config_not_empty(ruff_config_path):
    """Verify .ruff.toml is not empty."""
    assert ruff_config_path.stat().st_size > 0, "ruff config file must not be empty"

def test_ruff_config_valid_toml(ruff_config_path):
    """Verify .ruff.toml is valid TOML and contains 'lint' section."""
    with open(ruff_config_path, "r") as f:
        config = toml.load(f)
    assert "lint" in config, "ruff config must contain [lint] section"
    assert "select" in config["lint"], "ruff config must specify rules to select"

def test_black_config_exists(pyproject_path):
    """Verify pyproject.toml exists."""
    assert pyproject_path.exists(), "pyproject.toml must exist"

def test_black_config_not_empty(pyproject_path):
    """Verify pyproject.toml is not empty."""
    assert pyproject_path.stat().st_size > 0, "pyproject.toml must not be empty"

def test_black_config_valid_toml(pyproject_path):
    """Verify pyproject.toml is valid TOML and contains 'tool.black' section."""
    with open(pyproject_path, "r") as f:
        config = toml.load(f)
    assert "tool" in config, "pyproject.toml must contain [tool] section"
    assert "black" in config["tool"], "pyproject.toml must contain [tool.black] section"
    assert "line-length" in config["tool"]["black"], "black config must specify line-length"
    assert config["tool"]["black"]["line-length"] == 88, "black line-length should be 88"

def test_requirements_includes_dev_tools(requirements_path):
    """Verify requirements.txt includes black and ruff."""
    content = requirements_path.read_text()
    assert "black" in content.lower(), "requirements.txt must include black"
    assert "ruff" in content.lower(), "requirements.txt must include ruff"