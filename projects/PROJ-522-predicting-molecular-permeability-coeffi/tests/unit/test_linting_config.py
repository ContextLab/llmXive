"""
Unit tests to verify linting configuration files exist and are valid.
"""
import os
import subprocess
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUFF_CONFIG_PATH = os.path.join(PROJECT_ROOT, "code", "config", "ruff.toml")

def test_ruff_config_exists():
    """Verify ruff.toml configuration file exists."""
    assert os.path.isfile(RUFF_CONFIG_PATH), f"Ruff config not found at {RUFF_CONFIG_PATH}"

def test_ruff_config_syntax():
    """Verify ruff can parse the configuration file."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", RUFF_CONFIG_PATH, "--isolated"],
        capture_output=True,
        text=True,
        timeout=30
    )
    # We expect this to potentially return non-zero if there are lint errors in the code,
    # but it must NOT fail due to config parsing errors.
    # A config parse error usually results in a specific stderr message or exit code 2.
    # We check that the command ran and didn't crash on parsing.
    assert "Failed to parse" not in result.stderr, f"Ruff config parsing failed: {result.stderr}"

def test_black_available():
    """Verify black is installed and runnable."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0, "Black is not installed or not runnable"
    assert "black" in result.stdout.lower()