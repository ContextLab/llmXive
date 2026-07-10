"""
Unit tests for linting and formatting configuration.
"""
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import pytest


@pytest.fixture
def code_dir():
    """Get the code directory path."""
    return Path(__file__).parent.parent.parent / "code"


def test_ruff_config_exists(code_dir):
    """Test that ruff configuration file exists."""
    ruff_config = code_dir / "ruff.toml"
    assert ruff_config.exists(), "ruff.toml configuration file should exist"


def test_black_config_exists(code_dir):
    """Test that black configuration file exists."""
    pyproject = code_dir / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml should exist"
    
    with open(pyproject, "r") as f:
        content = f.read()
        assert "[tool.black]" in content, "pyproject.toml should contain [tool.black] section"


def test_ruff_command_exists():
    """Test that ruff command is available."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "ruff" in result.stdout.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("ruff is not installed or not in PATH")


def test_black_command_exists():
    """Test that black command is available."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "black" in result.stdout.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("black is not installed or not in PATH")


def test_config_linting_script_exists(code_dir):
    """Test that the configuration script exists."""
    script = code_dir / "config_linting.py"
    assert script.exists(), "config_linting.py should exist"


def test_config_linting_script_executable(code_dir):
    """Test that the configuration script can be executed."""
    script = code_dir / "config_linting.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            check=True,
            capture_output=True,
            text=True,
            cwd=code_dir
        )
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        pytest.fail(f"config_linting.py failed to execute: {e.stderr}")