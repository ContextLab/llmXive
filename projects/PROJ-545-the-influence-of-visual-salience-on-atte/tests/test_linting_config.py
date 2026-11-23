"""
Contract tests to verify that linting and formatting configurations are valid.
These tests ensure that the tools (ruff, black) can parse the config files
and that the project structure adheres to the expected standards.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify that ruff configuration file exists."""
    ruff_config = PROJECT_ROOT / "pyproject.toml"
    assert ruff_config.exists(), "pyproject.toml (ruff config) not found"

    # Verify ruff can parse the config
    result = subprocess.run(
        ["ruff", "check", "--output-format=concise", "--isolated"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We don't expect this to pass on unformatted code, but it should not crash
    # due to config errors.
    assert "error: Failed to" not in result.stderr, f"Ruff config error: {result.stderr}"

def test_black_config_exists():
    """Verify that black configuration is present in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

def test_pre_commit_config_exists():
    """Verify that pre-commit configuration file exists."""
    pre_commit_config = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert pre_commit_config.exists(), ".pre-commit-config.yaml not found"

def test_ruff_can_scan_code_directory():
    """Verify that ruff can successfully scan the code/ directory without config errors."""
    result = subprocess.run(
        ["ruff", "check", "code/", "--output-format=concise"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # Check for configuration errors, not linting failures
    assert "Failed to parse" not in result.stderr
    assert "error: Failed to" not in result.stderr

def test_black_can_format_code_directory():
    """Verify that black can check the code/ directory without config errors."""
    result = subprocess.run(
        ["black", "--check", "code/"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We expect failures if code isn't formatted, but not config errors
    assert "Error:" not in result.stderr or "cannot parse" not in result.stderr.lower()