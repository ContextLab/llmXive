"""
Tests to verify that linting and formatting configurations are present and valid.
"""
import os
import sys
import subprocess
import tomllib
from pathlib import Path

import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the code directory."""
    pyproject_path = code_dir / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_pyproject_toml_valid():
    """Test that pyproject.toml is valid TOML and contains required sections."""
    pyproject_path = code_dir / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        try:
            config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML in pyproject.toml: {e}")

    assert "tool" in config, "Missing 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "Missing 'black' configuration in pyproject.toml"
    assert "ruff" in config["tool"], "Missing 'ruff' configuration in pyproject.toml"

def test_black_configuration():
    """Test that Black configuration is present and valid."""
    pyproject_path = code_dir / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing 'line-length' in Black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "target-version" in black_config, "Missing 'target-version' in Black config"
    assert "py311" in black_config["target-version"], "Black should target Python 3.11"

def test_ruff_configuration():
    """Test that Ruff configuration is present and valid."""
    pyproject_path = code_dir / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "Missing 'line-length' in Ruff config"
    assert ruff_config["line-length"] == 88, "Ruff line-length should be 88"
    assert "select" in ruff_config, "Missing 'select' in Ruff config"
    assert "target-version" in ruff_config, "Missing 'target-version' in Ruff config"
    assert ruff_config["target-version"] == "py311", "Ruff should target Python 3.11"

def test_ruff_check_command_runs():
    """Test that ruff check command can be executed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Ruff returns 0 if no errors, 1 if errors found, 2 if config error
        # We just want to ensure it runs without crashing
        assert result.returncode in [0, 1], f"Ruff check failed with code {result.returncode}: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")
    except FileNotFoundError:
        pytest.skip("Ruff not installed in test environment")

def test_black_command_runs():
    """Test that black check command can be executed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 0 if formatted correctly, 1 if not
        assert result.returncode in [0, 1], f"Black check failed with code {result.returncode}: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")
    except FileNotFoundError:
        pytest.skip("Black not installed in test environment")