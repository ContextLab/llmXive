"""
Unit tests for linting and formatting configuration.
These tests verify that the configuration files (pyproject.toml, .ruff.toml, .black.toml)
exist and contain the expected settings for Black and Ruff.
"""
import os
import pytest
from pathlib import Path
import tomllib

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml exists."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist in the project root."

def test_pyproject_toml_has_black_config(project_root):
    """Test that pyproject.toml contains Black configuration."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist."
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml should contain [tool.black] section."
    assert "line-length = 88" in content, "Black line-length should be 88."
    assert "target-version" in content, "Black target-version should be specified."

def test_pyproject_toml_has_ruff_config(project_root):
    """Test that pyproject.toml contains Ruff configuration."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist."
    
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml should contain [tool.ruff] section."
    assert "select" in content, "Ruff select list should be specified."
    assert "ignore" in content, "Ruff ignore list should be specified."

def test_ruff_toml_exists(project_root):
    """Test that .ruff.toml exists."""
    ruff_toml_path = project_root / ".ruff.toml"
    assert ruff_toml_path.exists(), ".ruff.toml should exist in the project root."

def test_black_toml_exists(project_root):
    """Test that .black.toml exists."""
    black_toml_path = project_root / ".black.toml"
    assert black_toml_path.exists(), ".black.toml should exist in the project root."

def test_ruff_config_valid_syntax(project_root):
    """Test that .ruff.toml is valid TOML syntax."""
    ruff_toml_path = project_root / ".ruff.toml"
    try:
        with open(ruff_toml_path, "rb") as f:
            tomllib.load(f)
    except Exception as e:
        pytest.fail(f".ruff.toml is not valid TOML: {e}")

def test_black_config_valid_syntax(project_root):
    """Test that .black.toml is valid TOML syntax."""
    black_toml_path = project_root / ".black.toml"
    try:
        with open(black_toml_path, "rb") as f:
            tomllib.load(f)
    except Exception as e:
        pytest.fail(f".black.toml is not valid TOML: {e}")