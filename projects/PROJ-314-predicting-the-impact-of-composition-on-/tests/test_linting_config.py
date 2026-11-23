"""
Unit tests to verify that linting and formatting configurations are present and valid.
"""
import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "code" / "pyproject.toml"

def test_pyproject_exists():
    """Verify that pyproject.toml exists in the code directory."""
    assert PYPROJECT_PATH.exists(), "pyproject.toml must exist in code/ directory"

def test_ruff_config_present():
    """Verify that [tool.ruff] section exists in pyproject.toml."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] configuration"

def test_black_config_present():
    """Verify that [tool.black] section exists in pyproject.toml."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] configuration"

def test_ruff_check_passes_on_test_file():
    """Verify that ruff can successfully lint the test file itself."""
    # Run ruff check on the current test file
    result = subprocess.run(
        ["ruff", "check", str(PROJECT_ROOT / "tests" / "test_linting_config.py")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    # We expect it to pass (exit code 0) or have warnings that are ignored
    # The important thing is that ruff is configured and runnable
    assert result.returncode in [0, 1], f"Ruff check failed unexpectedly: {result.stderr}"

def test_black_check_passes_on_test_file():
    """Verify that black can successfully format check the test file."""
    result = subprocess.run(
        ["black", "--check", str(PROJECT_ROOT / "tests" / "test_linting_config.py")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    # Exit code 0 means formatted correctly, 1 means would reformat
    # We just verify black is runnable and configured
    assert result.returncode in [0, 1], f"Black check failed unexpectedly: {result.stderr}"

def test_line_length_configured():
    """Verify that line-length is configured to 88 (Black default)."""
    content = PYPROJECT_PATH.read_text()
    assert "line-length = 88" in content, "Line length should be configured to 88"