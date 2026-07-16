"""Tests to verify linting and formatting configuration compliance."""
import subprocess
import os
import sys

def test_ruff_check_passes():
    """Ensure ruff check passes on the codebase."""
    code_root = os.path.join(os.path.dirname(__file__), "..")
    result = subprocess.run(
        ["ruff", "check", code_root],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    # If ruff is not installed, skip or fail depending on env
    if result.returncode == 0:
        return
    # Allow failure if ruff isn't installed in CI environment
    if "ruff: command not found" in result.stderr:
        pytest.skip("ruff not installed")
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Ensure black check passes on the codebase."""
    code_root = os.path.join(os.path.dirname(__file__), "..")
    result = subprocess.run(
        ["black", "--check", code_root],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    if "black: command not found" in result.stderr:
        pytest.skip("black not installed")
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"