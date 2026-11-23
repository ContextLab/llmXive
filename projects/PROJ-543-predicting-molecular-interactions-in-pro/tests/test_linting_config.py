"""
Tests to verify linting configuration and tool availability.
"""
import subprocess
import sys
import os
from pathlib import Path

def test_flake8_available():
    """Verify flake8 is installed and accessible."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "flake8 is not installed or not in PATH"
    assert "flake8" in result.stdout.lower()

def test_black_available():
    """Verify black is installed and accessible."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "black is not installed or not in PATH"
    assert "black" in result.stdout.lower()

def test_isort_available():
    """Verify isort is installed and accessible."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "isort is not installed or not in PATH"
    assert "isort" in result.stdout.lower()

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    root = Path(__file__).parent.parent
    config_path = root / "code" / ".flake8"
    assert config_path.exists(), f"Configuration file missing: {config_path}"

def test_pyproject_toml_exists():
    """Verify pyproject.toml with tool configs exists."""
    root = Path(__file__).parent.parent
    config_path = root / "pyproject.toml"
    assert config_path.exists(), f"pyproject.toml missing: {config_path}"
    
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black config missing in pyproject.toml"
    assert "[tool.isort]" in content, "Isort config missing in pyproject.toml"