"""
Test to verify that linting configuration is properly set up (T003).
"""
import os
import toml
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Test that .ruff.toml configuration file exists."""
    project_root = Path(__file__).parent.parent
    ruff_config = project_root / "code" / ".ruff.toml"
    assert ruff_config.exists(), f"Ruff config not found at {ruff_config}"

def test_ruff_config_valid():
    """Test that .ruff.toml is valid TOML."""
    project_root = Path(__file__).parent.parent
    ruff_config = project_root / "code" / ".ruff.toml"
    try:
        with open(ruff_config, "r") as f:
            toml.load(f)
    except Exception as e:
        pytest.fail(f"Invalid TOML in {ruff_config}: {e}")

def test_pyproject_black_config():
    """Test that pyproject.toml contains black configuration."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "code" / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml not found at {pyproject}"

    with open(pyproject, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "Missing 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "Missing 'black' configuration in pyproject.toml"
    assert "line-length" in config["tool"]["black"], "Missing 'line-length' in black config"

def test_black_is_installable():
    """Test that black can be imported (if installed)."""
    try:
        import black
    except ImportError:
        pytest.skip("black is not installed in this environment")

def test_ruff_is_installable():
    """Test that ruff can be imported (if installed)."""
    try:
        import ruff
    except ImportError:
        pytest.skip("ruff is not installed in this environment")