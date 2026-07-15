"""
Tests to verify that linting and formatting tools are configured correctly.
These tests ensure that ruff and black are installed and can be invoked.
"""
import subprocess
import sys
import os

def test_ruff_is_installed():
    """Verify ruff is available in the environment."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("ruff is not installed or not in PATH")

def test_black_is_installed():
    """Verify black is available in the environment."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("black is not installed or not in PATH")

def test_ruff_config_exists():
    """Verify ruff.toml exists in the code directory."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "code", "ruff.toml")
    assert os.path.exists(config_path), f"ruff.toml not found at {config_path}"

def test_black_config_exists():
    """Verify pyproject.toml contains black configuration."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "code", "pyproject.toml")
    assert os.path.exists(config_path), f"pyproject.toml not found at {config_path}"
    
    with open(config_path, "r") as f:
        content = f.read()
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"