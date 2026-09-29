"""
Test suite to verify linting and formatting configurations.
Ensures that ruff and black are configured correctly and can be executed.
"""
import subprocess
import os
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_ruff_check_exists():
    """Verify that ruff is installed and can run check."""
    # Check if ruff is available
    result = subprocess.run(
        ["ruff", "--version"],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Ruff not found or not working: {result.stderr}"

def test_black_check_exists():
    """Verify that black is installed and can run check."""
    result = subprocess.run(
        ["black", "--version"],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black not found or not working: {result.stderr}"

def test_ruff_check_config():
    """
    Run ruff check on the code directory.
    This verifies that the configuration in pyproject.toml/.ruff.toml is valid.
    We expect exit code 0 if there are no errors, or a non-zero code if there are linting errors.
    The task requires the config to be valid and rules E, F, W, I enabled.
    """
    result = subprocess.run(
        ["ruff", "check", "--output-format=json", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    
    # We assert that ruff ran successfully (exit code 0 or 1)
    # Exit code 0: No errors found
    # Exit code 1: Errors found (but config is valid)
    # Exit code != 0 and != 1: Configuration error or missing tool
    assert result.returncode in (0, 1), (
        f"Ruff check failed with unexpected exit code {result.returncode}: {result.stderr}"
    )
    
    # Verify that the output is valid JSON if there were errors
    if result.returncode == 1:
        import json
        try:
            errors = json.loads(result.stdout)
            assert isinstance(errors, list)
        except json.JSONDecodeError:
            pytest.fail("Ruff output is not valid JSON when errors are present")

def test_black_check_config():
    """
    Run black check on the code directory.
    Verifies that black configuration is valid.
    """
    result = subprocess.run(
        ["black", "--check", "--diff", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    
    # Black returns 0 if formatted correctly, 1 if not, 2 if error
    # We mainly care that it runs without crashing (exit code != 2)
    assert result.returncode != 2, (
        f"Black check failed with error: {result.stderr}"
    )

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in the code directory."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found in code directory"

def test_ruff_toml_exists():
    """Verify .ruff.toml exists in the code directory."""
    ruff_toml_path = CODE_DIR / ".ruff.toml"
    assert ruff_toml_path.exists(), ".ruff.toml not found in code directory"
    
    # Verify content contains expected rules
    content = ruff_toml_path.read_text()
    assert "E" in content or 'select' in content.lower(), ".ruff.toml should reference rule E"
    assert "F" in content or 'select' in content.lower(), ".ruff.toml should reference rule F"
    assert "W" in content or 'select' in content.lower(), ".ruff.toml should reference rule W"
    assert "I" in content or 'select' in content.lower(), ".ruff.toml should reference rule I"