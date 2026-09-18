"""
Unit tests for linting and formatting configuration.
These tests verify that the configuration files exist and contain valid settings.
"""
import os
import sys
import pytest
from pathlib import Path
import tomli

# Add parent directory to path to import project modules if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def test_ruff_config_exists():
    """Test that .ruff.toml configuration file exists."""
    project_root = get_project_root()
    ruff_config = project_root / ".ruff.toml"
    assert ruff_config.exists(), ".ruff.toml configuration file is missing"

def test_black_config_exists():
    """Test that .black.toml configuration file exists."""
    project_root = get_project_root()
    black_config = project_root / ".black.toml"
    assert black_config.exists(), ".black.toml configuration file is missing"

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists and contains tool configurations."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml is missing"

    with open(pyproject, "rb") as f:
        content = tomli.load(f)

    assert "tool" in content, "pyproject.toml missing [tool] section"
    assert "black" in content["tool"], "pyproject.toml missing [tool.black] section"
    assert "ruff" in content["tool"], "pyproject.toml missing [tool.ruff] section"

def test_ruff_config_valid():
    """Test that .ruff.toml is a valid TOML file."""
    project_root = get_project_root()
    ruff_config = project_root / ".ruff.toml"

    with open(ruff_config, "rb") as f:
        try:
            content = tomli.load(f)
            assert "lint" in content, ".ruff.toml missing [lint] section"
        except Exception as e:
            pytest.fail(f".ruff.toml is not a valid TOML file: {e}")

def test_black_config_valid():
    """Test that .black.toml is a valid TOML file."""
    project_root = get_project_root()
    black_config = project_root / ".black.toml"

    with open(black_config, "rb") as f:
        try:
            content = tomli.load(f)
            assert "tool" in content, ".black.toml missing [tool] section"
            assert "black" in content["tool"], ".black.toml missing [tool.black] section"
        except Exception as e:
            pytest.fail(f".black.toml is not a valid TOML file: {e}")

def test_line_length_consistency():
    """Test that line length is consistent across configuration files."""
    project_root = get_project_root()

    # Check .ruff.toml
    with open(project_root / ".ruff.toml", "rb") as f:
        ruff_config = tomli.load(f)
    ruff_line_length = ruff_config.get("line-length", 88)

    # Check pyproject.toml [tool.black]
    with open(project_root / "pyproject.toml", "rb") as f:
        pyproject_config = tomli.load(f)
    black_line_length = pyproject_config.get("tool", {}).get("black", {}).get("line-length", 88)

    # Check pyproject.toml [tool.ruff]
    ruff_pyproject_line_length = pyproject_config.get("tool", {}).get("ruff", {}).get("line-length", 88)

    assert ruff_line_length == black_line_length, f"Line length mismatch: ruff={ruff_line_length}, black={black_line_length}"
    assert ruff_line_length == ruff_pyproject_line_length, f"Line length mismatch: ruff.toml={ruff_line_length}, pyproject.toml ruff={ruff_pyproject_line_length}"