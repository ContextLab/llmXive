"""
Tests to verify that linting and formatting configurations are correctly set up.
These tests ensure that ruff and black configurations exist and are valid.
"""
import os
import subprocess
import tempfile
import tomlkit  # type: ignore
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUFF_CONFIG_PATH = os.path.join(PROJECT_ROOT, "code", "ruff.toml")
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "pyproject.toml")

def test_ruff_config_exists():
    """Verify ruff.toml configuration file exists."""
    assert os.path.exists(RUFF_CONFIG_PATH), f"Ruff config not found at {RUFF_CONFIG_PATH}"

def test_black_config_in_pyproject():
    """Verify black configuration exists in pyproject.toml."""
    assert os.path.exists(PYPROJECT_PATH), f"pyproject.toml not found at {PYPROJECT_PATH}"
    
    with open(PYPROJECT_PATH, "r") as f:
        content = f.read()
    
    # Simple check for black section
    assert "[tool.black]" in content, "Black configuration section missing from pyproject.toml"

def test_ruff_check_syntax():
    """Run ruff check on the codebase to ensure configuration is valid and no immediate errors."""
    # Run ruff check on the code directory
    result = subprocess.run(
        ["ruff", "check", "code/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We expect it to run without crashing. 
    # It might find linting errors in existing code, but the config itself must be valid.
    # If the config is invalid, ruff usually exits with code 2 or throws an error in stderr.
    # For this task, we primarily ensure the command runs without config errors.
    # If the exit code is 1, it means linting violations found (OK).
    # If exit code is 0, no violations (OK).
    # If exit code is 2 or higher, likely config error or crash (Fail).
    assert result.returncode < 2, f"Ruff check failed due to config error: {result.stderr}"

def test_black_check_syntax():
    """Run black check on the codebase to ensure configuration is valid."""
    result = subprocess.run(
        ["black", "--check", "code/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # Black --check returns 0 if OK, 1 if violations found.
    # It returns 2 if there is a config error or crash.
    assert result.returncode < 2, f"Black check failed due to config error: {result.stderr}"

def test_ruff_config_syntax_validity():
    """Parse ruff.toml to ensure it is valid TOML."""
    # ruff.toml uses TOML format
    with open(RUFF_CONFIG_PATH, "r") as f:
        try:
            tomlkit.parse(f.read())
        except Exception as e:
            pytest.fail(f"ruff.toml is not valid TOML: {e}")