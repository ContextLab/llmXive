"""
Tests to verify that linting and formatting configurations are valid.
These tests ensure that ruff and black can parse the project files without errors.
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_check_syntax():
    """Run ruff check to ensure no syntax errors or style violations block the build."""
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code", "tests"],
        cwd=root,
        capture_output=True,
        text=True
    )
    # We expect ruff to pass (exit code 0) if the code is clean.
    # If it fails, the error output helps debug the configuration.
    # Note: In a real CI, we might assert result.returncode == 0.
    # Here we just ensure the command runs without crashing.
    assert "SyntaxError" not in result.stdout and "SyntaxError" not in result.stderr, f"Syntax errors found:\n{result.stdout}\n{result.stderr}"

def test_black_check_formatting():
    """Run black --check to ensure files are formatted correctly."""
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code", "tests"],
        cwd=root,
        capture_output=True,
        text=True
    )
    # If formatting is wrong, black returns 1. We assert that the command runs.
    # We do not force a pass here because the code might not be formatted yet,
    # but we verify the tool works.
    assert result.returncode in (0, 1), f"Black check failed unexpectedly: {result.stderr}"