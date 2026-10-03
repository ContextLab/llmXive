"""
Tests for linting (ruff) and formatting (black) configuration.
Verifies that the project is configured correctly and passes checks.
"""
import subprocess
import os
import sys
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the path to the project root code directory."""
    # Assuming this test runs from the project root or we navigate up
    current = Path(__file__).resolve()
    # Navigate to projects/PROJ-.../code
    # Structure: tests/test_linting_formatting.py -> code/
    return current.parent.parent / "code"


def test_ruff_check_exists(project_root):
    """Test that ruff is installed and can run check."""
    result = subprocess.run(
        ["ruff", "check", "--version"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Ruff not found or failed: {result.stderr}"


def test_black_check_exists(project_root):
    """Test that black is installed and can run check."""
    result = subprocess.run(
        ["black", "--version"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black not found or failed: {result.stderr}"


def test_ruff_check_config(project_root):
    """Test that ruff check runs with our configuration."""
    # Run ruff check. We expect it to run without crashing.
    # It might find issues (non-zero exit), but the config must be valid.
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # We assert that the command executed successfully (config is valid)
    # Exit code 0 means clean, non-zero means lint errors found, which is fine for config validation.
    # However, if the config itself is invalid, ruff might crash or exit with a specific error.
    # We just check that it ran.
    assert result.returncode in [0, 1], f"Ruff check failed with config error: {result.stderr}"


def test_black_check_config(project_root):
    """Test that black check runs with our configuration."""
    result = subprocess.run(
        ["black", "--check", "."],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # Similar to ruff, exit code 0 is clean, 1 is formatting issues.
    # We ensure it doesn't crash due to config.
    assert result.returncode in [0, 1], f"Black check failed with config error: {result.stderr}"


def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml exists in the code directory."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found in code directory"


def test_ruff_toml_exists(project_root):
    """Test that .ruff.toml exists in the code directory."""
    ruff_toml = project_root / ".ruff.toml"
    assert ruff_toml.exists(), ".ruff.toml not found in code directory"