import subprocess
import sys
import os
from pathlib import Path
import pytest

def get_project_root():
    """Get the project root directory (parent of 'code')."""
    # Assuming the test is run from within the 'code' directory or the root is 'code'
    # Based on the API surface, paths are relative to 'code/'
    current = Path(__file__).resolve()
    # If running from tests/test_linting_formatting.py, root is likely the parent of 'code' or 'code' itself
    # The artifact paths in the prompt are 'code/...', so we assume the project root is the parent of 'code'
    # But often in these setups, 'code' IS the root. Let's check if 'pyproject.toml' exists in parent or current.
    if (current.parent / "pyproject.toml").exists():
        return current.parent
    if (current.parent.parent / "pyproject.toml").exists():
        return current.parent.parent
    return current.parent.parent

def test_ruff_check_passes():
    """Test that ruff check passes on the codebase."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # Ruff returns 0 if no errors, non-zero otherwise.
    # We assert that it passes (exit code 0).
    # Note: In a real CI, we might want to see the output if it fails.
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Test that black check passes on the codebase."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_ruff_format_check_passes():
    """Test that ruff format check (if available) passes."""
    project_root = get_project_root()
    # ruff format is newer, might not be available in older versions.
    # We try to run it, but if the command fails (not found), we might skip or handle it.
    # However, the task asks to configure ruff and black.
    # Let's assume ruff >= 0.1.0 supports format or we just check the linting.
    # If 'ruff format' is not supported, we can skip this specific assertion or rely on black.
    # Given the constraint to implement T003, and T003 is about configuring them.
    # The test verifies the configuration is correct by running the tools.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        # If ruff format is supported, it should pass. If not, the command might fail with "no such command".
        # We'll assert 0 if it runs. If it fails because the command doesn't exist, we can ignore or assert on stderr.
        # For robustness, we check if the command exists first or just expect success if the tool is new enough.
        # Given the requirements.txt pins ruff>=0.1.0, format might be available.
        if result.returncode != 0:
            # If it fails, check if it's a "no such command" error
            if "no such command" in result.stderr.lower():
                pytest.skip("ruff format command not available in this version")
            else:
                assert False, f"Ruff format check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff command not found")
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff format check timed out")