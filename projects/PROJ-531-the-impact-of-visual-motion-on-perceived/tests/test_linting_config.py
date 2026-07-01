"""
Test suite to verify linting and formatting configuration.
This test ensures that the project's linting setup is functional.
"""
import subprocess
import sys
import os
import pytest

def test_ruff_is_installed():
    """Verify that ruff is available in the environment."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("Ruff is not installed or not in PATH")

def test_black_is_installed():
    """Verify that black is available in the environment."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("Black is not installed or not in PATH")

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and contains linting config."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml not found"
    
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"

def test_run_lint_script_exists():
    """Verify that the run_lint.py script exists."""
    assert os.path.exists("code/run_lint.py"), "code/run_lint.py not found"

def test_run_format_script_exists():
    """Verify that the run_format.py script exists."""
    assert os.path.exists("code/run_format.py"), "code/run_format.py not found"