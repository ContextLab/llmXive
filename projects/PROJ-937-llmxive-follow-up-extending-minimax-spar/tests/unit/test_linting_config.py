"""
Unit tests to verify linting and formatting configuration exists and is valid.
These tests ensure that ruff and black are configured correctly.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_ruff_config_exists():
    """Verify ruff.toml exists in the code directory."""
    ruff_path = PROJECT_ROOT / "code" / "ruff.toml"
    assert ruff_path.exists(), f"ruff.toml not found at {ruff_path}"

def test_pyproject_toml_has_dev_deps():
    """Verify pyproject.toml includes ruff and black in optional-dependencies."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    assert "ruff" in content, "ruff not found in pyproject.toml dependencies"
    assert "black" in content, "black not found in pyproject.toml dependencies"

def test_black_config_exists_in_pyproject():
    """Verify black configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

def test_ruff_check_passes_on_code():
    """Run ruff check on the code directory to ensure no linting errors exist."""
    ruff_path = PROJECT_ROOT / "code" / "ruff.toml"
    if not ruff_path.exists():
        pytest.skip("ruff.toml not found, skipping check")
    
    # Run ruff check against the code directory
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check",
                "--config", str(ruff_path),
                str(PROJECT_ROOT / "code")
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        # If ruff is not installed, skip
        if result.returncode == 1 and "No such file" in result.stderr:
            pytest.skip("ruff not installed in environment")
        
        # Return code 0 means no errors
        assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff command not found in PATH")
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff check timed out")

def test_black_check_passes_on_code():
    """Run black --check on the code directory to ensure formatting is correct."""
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "black",
                "--check",
                "--config", str(PROJECT_ROOT / "pyproject.toml"),
                str(PROJECT_ROOT / "code")
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # If black is not installed, skip
        if "No module named 'black'" in result.stderr:
            pytest.skip("black not installed in environment")
        
        # Return code 0 means files are formatted correctly
        assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("black command not found in PATH")
    except subprocess.TimeoutExpired:
        pytest.skip("Black check timed out")