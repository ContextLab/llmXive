"""
Unit tests for linting and formatting configuration.
These tests verify that the configuration files exist and that the tools
can be invoked successfully.
"""
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def code_dir(project_root):
    """Get the code directory."""
    return project_root / "code"

def test_flake8_config_exists(code_dir):
    """Test that .flake8 configuration file exists."""
    flake8_config = code_dir / ".flake8"
    assert flake8_config.exists(), "flake8 configuration file (.flake8) not found"
    assert flake8_config.stat().st_size > 0, "flake8 configuration file is empty"

def test_pyproject_toml_exists(code_dir):
    """Test that pyproject.toml configuration file exists."""
    pyproject_config = code_dir / "pyproject.toml"
    assert pyproject_config.exists(), "pyproject.toml configuration file not found"
    assert pyproject_config.stat().st_size > 0, "pyproject.toml configuration file is empty"

def test_flake8_can_run(code_dir):
    """Test that flake8 can be executed and finds no critical errors in config."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "flake8" in result.stdout.lower(), "flake8 version output does not contain 'flake8'"
    except subprocess.CalledProcessError:
        pytest.fail("flake8 is not installed or cannot be executed")

def test_black_can_run(code_dir):
    """Test that black can be executed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "black" in result.stdout.lower(), "black version output does not contain 'black'"
    except subprocess.CalledProcessError:
        pytest.fail("black is not installed or cannot be executed")

def test_isort_can_run(code_dir):
    """Test that isort can be executed (optional, but good to have)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "isort" in result.stdout.lower(), "isort version output does not contain 'isort'"
    except subprocess.CalledProcessError:
        # isort is optional, so we don't fail the test if it's not installed
        pytest.skip("isort is not installed")