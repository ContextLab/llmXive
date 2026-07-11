"""
Tests to verify linting and formatting configuration.
These tests ensure that ruff and black are correctly configured.
"""
import subprocess
import sys
from pathlib import Path

import pytest


def test_ruff_check_passes():
    """Verify that ruff check passes on the code directory."""
    project_root = Path(__file__).parent.parent
    ruff_cmd = [
        sys.executable, "-m", "ruff", "check", "code/",
        "--config", "pyproject.toml"
    ]
    result = subprocess.run(ruff_cmd, cwd=project_root, capture_output=True, text=True)
    
    # If ruff is not installed, skip the test (setup phase)
    if result.returncode == 1 and "No such file" in result.stderr:
        pytest.skip("Ruff not installed in environment")
    
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Verify that black check passes on the code directory."""
    project_root = Path(__file__).parent.parent
    black_cmd = [
        sys.executable, "-m", "black", "--check", "code/",
        "--config", "pyproject.toml"
    ]
    result = subprocess.run(black_cmd, cwd=project_root, capture_output=True, text=True)
    
    # If black is not installed, skip the test
    if result.returncode == 1 and "No such file" in result.stderr:
        pytest.skip("Black not installed in environment")
    
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"