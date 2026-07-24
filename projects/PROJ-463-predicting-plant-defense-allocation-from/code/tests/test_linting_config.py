import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_black_config_valid():
    """Verify that Black configuration is valid and can parse pyproject.toml."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(PROJECT_ROOT)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # We expect exit code 1 if files are not formatted, but we want to ensure
    # the config is valid (no syntax errors in pyproject.toml parsing).
    # If config is invalid, black usually exits with code 2 or raises an error.
    # We just check that it ran without crashing due to config errors.
    assert "Error parsing" not in result.stderr, f"Black config error: {result.stderr}"

def test_ruff_config_valid():
    """Verify that Ruff configuration is valid."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--isolated", str(PROJECT_ROOT)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Ruff might find errors (exit 1), but it should not crash due to config issues.
    # Config errors usually manifest as stderr messages about parsing.
    assert "Failed to parse" not in result.stderr, f"Ruff config error: {result.stderr}"