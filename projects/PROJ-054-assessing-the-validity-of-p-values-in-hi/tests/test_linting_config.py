"""
Test to verify that linting and formatting configurations are present and valid.
This ensures T003 is complete: ruff, black, and flake8 are configured.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

CONFIG_FILES = [
    PROJECT_ROOT / "pyproject.toml",
    PROJECT_ROOT / ".ruff.toml",
    PROJECT_ROOT / ".flake8",
]

def test_config_files_exist():
    """Verify that configuration files for linting and formatting exist."""
    missing = [f for f in CONFIG_FILES if not f.exists()]
    assert not missing, f"Missing configuration files: {missing}"

def test_pyproject_toml_has_black_config():
    """Verify pyproject.toml contains Black configuration."""
    content = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length" in content, "pyproject.toml missing Black line-length setting"

def test_pyproject_toml_has_ruff_config():
    """Verify pyproject.toml contains Ruff configuration."""
    content = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert "[tool.ruff]" in content, "pyproject.toml missing [tool.ruff] section"

@pytest.mark.skipif(
    not (subprocess.run(["which", "black"], capture_output=True).returncode == 0),
    reason="black not installed in environment",
)
def test_black_check_syntax_only():
    """
    Run black --check --diff on a small subset of files to ensure config works.
    We don't run full check as it might fail on unformatted code, but we verify
    the tool runs and reads the config.
    """
    # Just check if black can be invoked with the project config
    result = subprocess.run(
        ["black", "--check", "--diff", "--verbose", str(PROJECT_ROOT / "code")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # We expect it to potentially find formatting issues (returncode 1) or pass (0)
    # The key is that it runs without configuration errors (returncode 2 usually)
    # If it fails due to config parse error, that's a failure.
    # We allow 0 (all good) or 1 (needs formatting), but not 2+ (config error)
    assert result.returncode < 2, f"Black configuration error: {result.stderr}"

@pytest.mark.skipif(
    not (subprocess.run(["which", "ruff"], capture_output=True).returncode == 0),
    reason="ruff not installed in environment",
)
def test_ruff_check_syntax_only():
    """
    Run ruff check on the code directory to verify config is valid.
    """
    result = subprocess.run(
        ["ruff", "check", str(PROJECT_ROOT / "code")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Ruff returns 1 for linting errors, 0 for clean, >1 for errors
    # We just want to ensure it runs and reads config
    assert result.returncode < 2, f"Ruff configuration error: {result.stderr}"

@pytest.mark.skipif(
    not (subprocess.run(["which", "flake8"], capture_output=True).returncode == 0),
    reason="flake8 not installed in environment",
)
def test_flake8_check_syntax_only():
    """
    Run flake8 on the code directory to verify config is valid.
    """
    result = subprocess.run(
        ["flake8", str(PROJECT_ROOT / "code")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Flake8 returns 1 for linting errors, 0 for clean, >1 for errors
    assert result.returncode < 2, f"Flake8 configuration error: {result.stderr}"