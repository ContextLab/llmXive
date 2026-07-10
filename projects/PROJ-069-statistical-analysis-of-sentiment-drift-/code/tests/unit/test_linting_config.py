"""
Unit tests to verify that linting and formatting configurations are valid.
These tests ensure that the project's tooling (Black, Ruff) can be invoked
and that configuration files are syntactically correct.
"""
import subprocess
import sys
from pathlib import Path

import pytest


def get_project_root() -> Path:
    """Locate the project root (parent of code/)."""
    current = Path(__file__).resolve()
    # Traverse up until we find the 'code' directory or the root
    while current.parent != current:
        if (current / "code").exists():
            return current
        current = current.parent
    # Fallback: assume current directory is root if 'code' not found
    return Path.cwd()


@pytest.mark.unit
def test_ruff_check_syntax():
    """
    Verify that Ruff can run a syntax check on the codebase without errors
    related to configuration.
    """
    root = get_project_root()
    code_dir = root / "code"

    # Run ruff check on the code directory
    # We expect it to pass configuration parsing. Actual linting errors
    # might exist in code, but the config itself must be valid.
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(root / "code" / "pyproject.toml"), str(code_dir)],
        capture_output=True,
        text=True,
    )

    # If ruff is not installed, skip (environment might not have it yet)
    if "No module named 'ruff'" in result.stderr:
        pytest.skip("Ruff not installed in environment")

    # Configuration errors usually show up as exit code 2 or specific stderr messages
    # We primarily check that the config file is recognized and parsed.
    # A successful parse means the file structure is correct.
    assert "Failed to parse" not in result.stderr, f"Ruff config parse failed: {result.stderr}"


@pytest.mark.unit
def test_black_check_syntax():
    """
    Verify that Black can read the configuration and perform a check.
    """
    root = get_project_root()
    code_dir = root / "code"

    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(root / "code" / "pyproject.toml"), "--check", "--diff", str(code_dir)],
        capture_output=True,
        text=True,
    )

    if "No module named 'black'" in result.stderr:
        pytest.skip("Black not installed in environment")

    # Black exits with 0 if files are formatted correctly, 1 if they need reformatting.
    # We are testing that the CONFIG is valid, so we ensure it doesn't crash with a config error.
    assert "Configuration error" not in result.stderr, f"Black config error: {result.stderr}"


@pytest.mark.unit
def test_pyproject_exists():
    """Verify pyproject.toml exists in the code directory."""
    root = get_project_root()
    config_path = root / "code" / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml not found in code directory"
    assert config_path.stat().st_size > 0, "pyproject.toml is empty"