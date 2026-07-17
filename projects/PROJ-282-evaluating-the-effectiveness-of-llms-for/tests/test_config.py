"""
Tests for the configuration setup (T003).
Verifies that ruff and black configurations are syntactically valid and loadable.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent
CODE_DIR = ROOT_DIR / "code"

def test_ruff_config_exists():
    """Verify ruff.toml exists in the code directory."""
    ruff_path = CODE_DIR / "ruff.toml"
    assert ruff_path.exists(), f"ruff.toml not found at {ruff_path}"

def test_black_config_exists():
    """Verify pyproject.toml with black config exists."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"

def test_ruff_can_check_code():
    """Run ruff check on the code directory to ensure config is valid."""
    ruff_path = CODE_DIR / "ruff.toml"
    # Run ruff check on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(ruff_path), str(CODE_DIR)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR)
    )
    # We expect 0 (success) or 1 (linting errors found, but config is valid)
    # We specifically check that it didn't crash with a config error (exit code 2+)
    assert result.returncode < 2, f"Ruff config error: {result.stderr}"

def test_black_can_format_code():
    """Run black --check on the code directory to ensure config is valid."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(CODE_DIR / "pyproject.toml"), "--check", str(CODE_DIR)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR)
    )
    # Exit code 0: all clean
    # Exit code 1: would reformat (valid config, just needs formatting)
    # Exit code 2+: config error or syntax error
    assert result.returncode < 2, f"Black config error: {result.stderr}"