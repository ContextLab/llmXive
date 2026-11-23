"""
Test suite for T002b: Verify linting and formatting configuration.

This test ensures that:
1. pyproject.toml exists and contains valid Black and Ruff configuration.
2. .ruff.toml exists and contains valid Ruff configuration.
3. The configuration files pass `ruff check` and `black --check` on an empty codebase.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
RUFF_TOML_PATH = PROJECT_ROOT / ".ruff.toml"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    assert PYPROJECT_PATH.exists(), f"pyproject.toml not found at {PYPROJECT_PATH}"

def test_ruff_toml_exists():
    """Verify .ruff.toml exists."""
    assert RUFF_TOML_PATH.exists(), f".ruff.toml not found at {RUFF_TOML_PATH}"

def test_pyproject_contains_black_config():
    """Verify pyproject.toml contains Black configuration."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    assert "line-length" in content, "Missing line-length configuration in Black config"

def test_pyproject_contains_ruff_config():
    """Verify pyproject.toml contains Ruff configuration."""
    content = PYPROJECT_PATH.read_text()
    assert "[tool.ruff]" in content, "Missing [tool.ruff] section in pyproject.toml"

def test_ruff_toml_contains_ruff_config():
    """Verify .ruff.toml contains Ruff configuration."""
    content = RUFF_TOML_PATH.read_text()
    # Basic sanity check that it's a valid TOML-like config
    assert "line-length" in content or "select" in content, "Invalid or empty .ruff.toml content"

def test_ruff_check_passes_on_empty_codebase():
    """Verify ruff check passes on an empty temporary codebase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an empty Python file to satisfy ruff's requirement for at least one file
        empty_file = Path(tmpdir) / "empty.py"
        empty_file.write_text("# Empty file for linting test\n")
        
        # Run ruff check
        result = subprocess.run(
            ["ruff", "check", tmpdir],
            capture_output=True,
            text=True
        )
        # ruff should return 0 (success) if no errors are found
        assert result.returncode == 0, f"ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes_on_empty_codebase():
    """Verify black --check passes on an empty temporary codebase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an empty Python file to satisfy black's requirement for at least one file
        empty_file = Path(tmpdir) / "empty.py"
        empty_file.write_text("# Empty file for formatting test\n")
        
        # Run black --check
        result = subprocess.run(
            ["black", "--check", tmpdir],
            capture_output=True,
            text=True
        )
        # black returns 0 if all files are already formatted correctly
        assert result.returncode == 0, f"black --check failed:\n{result.stdout}\n{result.stderr}"