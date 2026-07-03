"""
Test suite to verify linting and formatting configuration.
These tests ensure that the project adheres to the defined style guides.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

# Get the project root (parent of 'tests' or 'code' directory)
PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_check_passes():
    """
    Verify that ruff check passes on the codebase.
    This ensures no linting errors exist.
    """
    # Run ruff check on the code directory
    result = subprocess.run(
        ["ruff", "check", "code/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # If ruff is not installed, skip the test (setup phase)
    if result.returncode == 127:
        pytest.skip("ruff not installed in environment")
    
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """
    Verify that black check passes on the codebase.
    This ensures code is properly formatted.
    """
    # Run black check on the code directory
    result = subprocess.run(
        ["black", "--check", "code/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # If black is not installed, skip the test (setup phase)
    if result.returncode == 127:
        pytest.skip("black not installed in environment")
    
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_ruff_format_check_passes():
    """
    Verify that ruff format check passes (alternative to black if configured).
    """
    result = subprocess.run(
        ["ruff", "format", "--check", "code/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 127:
        pytest.skip("ruff not installed in environment")
    
    # Note: ruff format might not be available in older versions, so we allow a specific error code if needed
    # For now, we expect it to pass or skip if not available
    if result.returncode != 0 and "No such file or directory" not in result.stderr and "unrecognized subcommand" not in result.stderr:
        # If it fails for a valid reason, assert it
        assert result.returncode == 0, f"Ruff format check failed:\n{result.stdout}\n{result.stderr}"