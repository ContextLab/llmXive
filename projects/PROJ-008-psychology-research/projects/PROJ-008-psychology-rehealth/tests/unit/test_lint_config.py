"""
Unit tests for linting and formatting configuration.
Verifies that ruff and black are configured correctly in pyproject.toml.
"""
import yaml
import toml
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

@pytest.fixture
def pyproject_data():
    if not PYPROJECT_PATH.exists():
        pytest.skip("pyproject.toml not found in project root")
    with open(PYPROJECT_PATH, "r") as f:
        return toml.load(f)

def test_black_config_exists(pyproject_data):
    """Verify black configuration section exists."""
    assert "tool" in pyproject_data
    assert "black" in pyproject_data["tool"]
    config = pyproject_data["tool"]["black"]
    assert config.get("line-length") == 88
    assert "py311" in config.get("target-version", [])

def test_ruff_config_exists(pyproject_data):
    """Verify ruff configuration section exists."""
    assert "tool" in pyproject_data
    assert "ruff" in pyproject_data["tool"]
    config = pyproject_data["tool"]["ruff"]
    assert config.get("line-length") == 88
    assert config.get("target-version") == "py311"
    assert "select" in config
    assert "E" in config["select"]
    assert "F" in config["select"]

def test_dev_dependencies_included(pyproject_data):
    """Verify ruff and black are listed in optional dependencies."""
    deps = pyproject_data.get("project", {}).get("optional-dependencies", {})
    dev_deps = deps.get("dev", [])
    dev_deps_str = " ".join(dev_deps)
    assert "ruff" in dev_deps_str
    assert "black" in dev_deps_str