"""
Tests to verify that the linting and formatting configurations (ruff and black)
are correctly set up and valid for Python 3.11.
"""
import subprocess
import sys
from pathlib import Path
import pytest
import tomli

# Determine project root relative to this test file
# Assuming structure: code/tests/test_linting_config.py -> root is code/
project_root = Path(__file__).parent.parent
pyproject_path = project_root / "pyproject.toml"


def test_black_config_valid():
    """Verify that black can parse its configuration from pyproject.toml."""
    if not pyproject_path.exists():
        pytest.fail("pyproject.toml not found at project root")

    # Run black --check on a dummy file to ensure config loads without error
    # We use --diff on a non-existent file or just check config validity
    # The most robust way is to run black --help or check version, but
    # to verify config specifically, we can try to run black on the current file.
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", __file__],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    # We expect exit code 0 if file is formatted correctly according to config,
    # or 1 if it needs formatting. We do NOT expect 2 (config error).
    # If the config is invalid, black exits with 2.
    if result.returncode == 2:
        pytest.fail(f"Black configuration error: {result.stderr}")


def test_ruff_config_valid():
    """Verify that ruff can parse its configuration from pyproject.toml."""
    if not pyproject_path.exists():
        pytest.fail("pyproject.toml not found at project root")

    # Run ruff check on the current file.
    # If config is invalid, ruff usually exits with non-zero and prints error.
    # We specifically check that it doesn't crash due to config parsing.
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", __file__],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Exit code 0: No issues found (or ignored)
    # Exit code 1: Issues found
    # Exit code 2: Configuration error or other fatal error
    if result.returncode == 2:
        pytest.fail(f"Ruff configuration error: {result.stderr}")

    # Optional: Verify target version is detected correctly
    version_result = subprocess.run(
        [sys.executable, "-m", "ruff", "version"],
        capture_output=True,
        text=True,
    )
    assert version_result.returncode == 0, "Ruff is not installed or not runnable"


def test_pyproject_toml_structure():
    """Ensure pyproject.toml contains required sections for black and ruff."""
    if not pyproject_path.exists():
        pytest.fail("pyproject.toml not found")

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] section"
    assert "ruff" in config["tool"] or "ruff" in config.get("tool", {}).get("lint", {}), \
        "Missing [tool.ruff] section (or [tool.ruff.lint])"

    # Verify Python 3.11 target
    assert config["tool"]["black"].get("target-version") == ["py311"], \
        "Black target-version must include py311"
    assert config["tool"]["ruff"].get("target-version") == "py311", \
        "Ruff target-version must be py311"