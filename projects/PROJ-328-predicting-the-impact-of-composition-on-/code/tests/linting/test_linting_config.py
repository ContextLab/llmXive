import subprocess
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify that a flake8 configuration file exists."""
    flake8_config = PROJECT_ROOT / "setup.cfg"
    assert flake8_config.exists(), "setup.cfg with flake8 config not found"
    content = flake8_config.read_text()
    assert "[flake8]" in content, "flake8 section missing in setup.cfg"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml with Black settings exists."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"

def test_black_can_parse_config():
    """Verify that black can successfully parse the configuration."""
    result = subprocess.run(
        ["black", "--check", "--diff", "--config", str(PROJECT_ROOT / "pyproject.toml")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We expect exit code 1 if files need formatting, but 0 if they don't.
    # The important thing is that black doesn't crash (exit code 2) due to config errors.
    assert result.returncode != 2, f"Black failed to parse config: {result.stderr}"

def test_flake8_can_parse_config():
    """Verify that flake8 can successfully parse the configuration."""
    result = subprocess.run(
        ["flake8", "--version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "flake8 command not found or failed"
    
    # Try running flake8 with our config on a dummy file to ensure it parses
    result = subprocess.run(
        ["flake8", "--config", str(PROJECT_ROOT / "setup.cfg"), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"flake8 failed to parse config: {result.stderr}"
