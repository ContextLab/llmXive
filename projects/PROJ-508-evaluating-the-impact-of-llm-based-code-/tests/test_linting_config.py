"""
Tests to verify that linting and formatting tools are configured correctly.
These tests ensure that the project adheres to the established code style.
"""
import subprocess
import sys
import os
from pathlib import Path

def test_black_is_installed():
    """Verify that Black is installed and accessible."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("Black is not installed or not in PATH")

def test_ruff_is_installed():
    """Verify that Ruff is installed and accessible."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("Ruff is not installed or not in PATH")

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and contains tool configurations."""
    root = Path(__file__).parent.parent
    config_file = root / "pyproject.toml"
    assert config_file.exists(), "pyproject.toml not found"
    
    content = config_file.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"

def test_black_formatting_check():
    """
    Verify that the codebase currently passes Black formatting checks.
    Note: If this fails, run 'black code/ tests/' to fix formatting.
    """
    root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            ["black", "--check", "code/", "tests/"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=60
        )
        # If exit code is 0, formatting is correct
        assert result.returncode == 0, f"Black formatting check failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        raise AssertionError("Black formatting check timed out")

def test_ruff_linting_check():
    """
    Verify that the codebase currently passes Ruff linting checks.
    Note: If this fails, run 'ruff check --fix code/ tests/' to fix issues.
    """
    root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "tests/"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=60
        )
        # If exit code is 0, linting is clean
        assert result.returncode == 0, f"Ruff linting check failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        raise AssertionError("Ruff linting check timed out")