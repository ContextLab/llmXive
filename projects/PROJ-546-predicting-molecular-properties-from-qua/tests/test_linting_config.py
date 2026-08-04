"""
Test task T003: Verify linting and formatting configuration.

This test ensures that ruff and black are correctly configured
and can be invoked without errors against the codebase.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    ruff_config = PROJECT_ROOT / "ruff.toml"
    assert ruff_config.exists(), "ruff.toml must exist in project root"
    content = ruff_config.read_text()
    assert "select" in content, "ruff.toml must define lint rules"
    assert "E" in content or "F" in content, "ruff.toml must include standard checks"

def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain black config"
    assert "line-length" in content, "black config must define line-length"

def test_ruff_can_run():
    """Verify ruff can be executed against the codebase."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(CODE_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # ruff returns 0 if no errors, 1 if errors found. 
        # We just want to ensure it runs and doesn't crash (exit code 2 or signal).
        assert result.returncode in (0, 1), f"Ruff crashed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff execution timed out")

def test_black_can_run():
    """Verify black can be executed against the codebase."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(CODE_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # black returns 0 if formatted correctly, 1 if changes needed.
        assert result.returncode in (0, 1), f"Black crashed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black execution timed out")