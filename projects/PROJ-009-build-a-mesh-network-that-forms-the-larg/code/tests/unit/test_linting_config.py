"""
Unit tests to verify that linting and formatting configurations are present and valid.
These tests ensure T003 (Configure linting and formatting) is complete.
"""
import os
import tomli
import pytest
from pathlib import Path

# Determine project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    assert config_path.exists(), f"pyproject.toml not found at {config_path}"

def test_pyproject_toml_has_black_config():
    """Verify Black configuration exists in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "black" in config["tool"], "No [tool.black] section in pyproject.toml"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Black line-length not configured"
    assert black_config["line-length"] == 88, "Black line-length should be 88"

def test_pyproject_toml_has_ruff_config():
    """Verify Ruff configuration exists in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "ruff" in config["tool"], "No [tool.ruff] section in pyproject.toml"
    
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "Ruff line-length not configured"
    assert ruff_config["line-length"] == 88, "Ruff line-length should be 88"

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), f".flake8 not found at {flake8_path}"

def test_flake8_config_valid():
    """Verify .flake8 contains expected settings."""
    flake8_path = PROJECT_ROOT / ".flake8"
    content = flake8_path.read_text()
    
    assert "max-line-length = 88" in content, "max-line-length not set to 88 in .flake8"
    assert "extend-ignore" in content, "extend-ignore not configured in .flake8"
    
def test_ruff_binary_available():
    """Verify ruff is installed and runnable (optional check)."""
    import subprocess
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, "ruff command failed"
        assert "ruff" in result.stdout.lower(), "ruff version output unexpected"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("ruff command timed out")

def test_black_binary_available():
    """Verify black is installed and runnable (optional check)."""
    import subprocess
    try:
        result = subprocess.run(
            ["black", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, "black command failed"
        assert "black" in result.stdout.lower(), "black version output unexpected"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("black command timed out")