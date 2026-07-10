"""
Tests to verify that linting and formatting configurations are valid.
These tests ensure that the project tools (ruff, black) can parse the config files.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_ruff_can_parse_config():
    """Verify ruff can load the configuration without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(PROJECT_ROOT / "pyproject.toml"), "--isolated", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    # We expect exit code 0 (success) or 1 (found issues), but NOT a config parsing error (usually 2)
    # The command might find issues in the code, but the config itself must be valid.
    # We specifically check that the config was loaded.
    assert "Failed to load configuration" not in result.stderr
    # If ruff runs, it means the config is valid.
    assert result.returncode in [0, 1]

def test_black_can_parse_config():
    """Verify black can load the configuration without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(PROJECT_ROOT / "pyproject.toml"), "--check", "--diff", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    # Black might return 1 if files are not formatted, but it must not return 2 (config error)
    assert "Could not find" not in result.stderr or "config" not in result.stderr
    # If black runs, it means the config is valid.
    assert result.returncode in [0, 1]