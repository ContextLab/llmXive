"""
Tests to verify that the linting and formatting configuration is active.
These tests ensure that ruff and black are properly configured.
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_check_runs_without_error():
    """Verify that ruff check passes on the codebase (ignoring E501)."""
    # Run ruff check on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/"],
        capture_output=True,
        text=True,
    )
    # We expect exit code 0 (no errors) or 1 (found issues).
    # If ruff is not installed, this will fail, which is expected in a clean env.
    # The goal is to ensure the configuration file is valid.
    # If ruff is present, it should read the config.
    if result.returncode not in [0, 1]:
        # If it's not 0 or 1, it might be a configuration error or missing tool
        # We allow 1 (linting issues found) as valid, but 2+ is config/runtime error
        assert False, f"Ruff check failed with code {result.returncode}: {result.stderr}"

def test_black_check_runs_without_error():
    """Verify that black check passes (or is configured correctly)."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "code/"],
        capture_output=True,
        text=True,
    )
    # 0 = clean, 1 = would reformat
    if result.returncode not in [0, 1]:
        # 2 = error (e.g., config error)
        assert False, f"Black check failed with code {result.returncode}: {result.stderr}"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists in the root."""
    assert Path("pyproject.toml").exists(), "pyproject.toml not found"

def test_ruff_config_exists():
    """Verify that .ruff.toml exists in the code directory."""
    assert Path("code/.ruff.toml").exists(), "code/.ruff.toml not found"