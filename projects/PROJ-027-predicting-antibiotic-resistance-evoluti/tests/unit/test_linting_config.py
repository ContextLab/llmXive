"""
Unit tests for linting and formatting configuration.
Verifies that ruff and black configurations are valid and present.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_ruff_config_exists():
    """Test that .ruff.toml configuration file exists."""
    config_path = Path("code/.ruff.toml")
    assert config_path.exists(), f"Configuration file {config_path} does not exist."


def test_black_config_exists():
    """Test that .black.toml configuration file exists."""
    config_path = Path("code/.black.toml")
    assert config_path.exists(), f"Configuration file {config_path} does not exist."


def test_ruff_syntax_check():
    """Test that ruff can parse the configuration and check syntax."""
    # Create a temporary file with valid Python code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 1\n")
        temp_file = f.name

    try:
        result = subprocess.run(
            ["ruff", "check", temp_file],
            capture_output=True,
            text=True,
            cwd="code",
        )
        # Ruff should run without crashing; exit code may be non-zero if issues found
        assert result.returncode in [0, 1], "Ruff check crashed unexpectedly."
    finally:
        os.unlink(temp_file)


def test_black_check_syntax():
    """Test that black can parse the configuration and check formatting."""
    # Create a temporary file with valid Python code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 1\n")
        temp_file = f.name

    try:
        result = subprocess.run(
            ["black", "--check", temp_file],
            capture_output=True,
            text=True,
            cwd="code",
        )
        # Black should run without crashing; exit code may be non-zero if formatting needed
        assert result.returncode in [0, 1], "Black check crashed unexpectedly."
    finally:
        os.unlink(temp_file)
