"""
Tests to verify that linting and formatting tools are correctly installed and configured.
"""
import subprocess
import sys
import os
import pytest

def test_black_installed():
    """Test that black is installed and can be invoked."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "black" in result.stdout.lower()

def test_flake8_installed():
    """Test that flake8 is installed and can be invoked."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "flake8" in result.stdout.lower()

def test_black_config_exists():
    """Test that pyproject.toml exists and contains black configuration."""
    assert os.path.exists("pyproject.toml")
    with open("pyproject.toml", "r") as f:
        content = f.read()
    assert "[tool.black]" in content

def test_flake8_config_exists():
    """Test that .flake8 exists and contains configuration."""
    assert os.path.exists(".flake8")
    with open(".flake8", "r") as f:
        content = f.read()
    assert "[flake8]" in content

def test_requirements_dev_includes_black():
    """Test that requirements-dev.txt includes black."""
    assert os.path.exists("requirements-dev.txt")
    with open("requirements-dev.txt", "r") as f:
        content = f.read()
    assert "black" in content
    assert "flake8" in content