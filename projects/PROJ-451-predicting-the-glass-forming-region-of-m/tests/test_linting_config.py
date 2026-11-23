"""
Test suite to verify linting and formatting configuration.
Ensures that ruff and black are correctly configured and can run against the codebase.
"""
import subprocess
import os
import pytest
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"
    ruff_toml = project_root / ".ruff.toml"

    assert pyproject.exists() or ruff_toml.exists(), (
        "Either pyproject.toml or .ruff.toml must exist for ruff configuration"
    )


def test_black_config_exists():
    """Verify black configuration file exists."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"
    black_toml = project_root / ".black.toml"

    assert pyproject.exists() or black_toml.exists(), (
        "Either pyproject.toml or .black.toml must exist for black configuration"
    )


def test_ruff_can_parse_config():
    """Verify ruff can successfully parse the configuration."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"

    # Run ruff check with --show-settings to validate config parsing
    # We don't need it to pass linting, just to parse the config
    result = subprocess.run(
        ["ruff", "check", "--config", str(pyproject), "--show-settings", "."],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )

    # If config is invalid, ruff will error on parsing.
    # We allow linting errors, but not config parsing errors.
    assert "error" not in result.stderr.lower() or "config" not in result.stderr.lower(), (
        f"Ruff failed to parse config: {result.stderr}"
    )


def test_black_can_parse_config():
    """Verify black can successfully parse the configuration."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"

    # Run black --check to validate config parsing
    result = subprocess.run(
        ["black", "--config", str(pyproject), "--check", "--diff", "."],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )

    # Black exits with 1 if files need formatting, which is OK.
    # It exits with error code if config is invalid.
    # We just want to ensure it didn't crash on config parsing.
    assert "error" not in result.stderr.lower() or "cannot" not in result.stderr.lower(), (
        f"Black failed to parse config: {result.stderr}"
    )


def test_requirements_includes_tools():
    """Verify requirements.txt includes ruff and black."""
    project_root = get_project_root()
    req_file = project_root / "requirements.txt"

    if not req_file.exists():
        pytest.skip("requirements.txt not found, skipping check")

    content = req_file.read_text().lower()
    assert "ruff" in content, "ruff must be in requirements.txt"
    assert "black" in content, "black must be in requirements.txt"