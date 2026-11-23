"""
Tests to verify that linting and formatting configurations are valid and loadable.
These tests ensure that ruff and black configurations exist and are syntactically correct.
"""
import os
import toml
import pytest
from pathlib import Path

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_pyproject_toml_valid():
    """Verify pyproject.toml is valid TOML and contains tool configurations."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    try:
        config = toml.load(pyproject_path)
    except Exception as e:
        pytest.fail(f"pyproject.toml is not valid TOML: {e}")

    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] configuration"
    assert "ruff" in config["tool"], "Missing [tool.ruff] configuration"

def test_black_config_present():
    """Verify Black configuration keys are present."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    config = toml.load(pyproject_path)
    black_config = config["tool"]["black"]

    assert "line-length" in black_config, "Missing 'line-length' in Black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "target-version" in black_config, "Missing 'target-version' in Black config"

def test_ruff_config_present():
    """Verify Ruff configuration keys are present."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    config = toml.load(pyproject_path)
    ruff_config = config["tool"]["ruff"]

    assert "line-length" in ruff_config, "Missing 'line-length' in Ruff config"
    assert "select" in ruff_config["lint"], "Missing 'select' in Ruff lint config"
    assert "exclude" in ruff_config, "Missing 'exclude' in Ruff config"

def test_ruff_toml_exists():
    """Verify .ruff.toml exists if used as override."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    # This is optional but good practice if we have a dedicated file
    # If it exists, it must be valid
    if ruff_path.exists():
        try:
            toml.load(ruff_path)
        except Exception as e:
            pytest.fail(f".ruff.toml is not valid TOML: {e}")

def test_black_toml_exists():
    """Verify .black.toml exists if used as override."""
    black_path = PROJECT_ROOT / ".black.toml"
    if black_path.exists():
        try:
            toml.load(black_path)
        except Exception as e:
            pytest.fail(f".black.toml is not valid TOML: {e}")