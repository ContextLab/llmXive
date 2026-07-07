import os
import pytest
import subprocess
import sys
from pathlib import Path


def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    assert os.path.exists(".flake8"), ".flake8 configuration file should exist"


def test_pyproject_black_config_exists():
    """Test that pyproject.toml with Black configuration exists."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml configuration file should exist"
    
    with open("pyproject.toml", "r") as f:
        content = f.read()
        assert "[tool.black]" in content, "pyproject.toml should contain Black configuration"


def test_flake8_command_available():
    """Test that flake8 command is available in the system."""
    try:
        result = subprocess.run(
            ["flake8", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert result.returncode == 0, "flake8 command should execute successfully"
    except subprocess.CalledProcessError:
        pytest.fail("flake8 command is not available")


def test_black_command_available():
    """Test that black command is available in the system."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert result.returncode == 0, "black command should execute successfully"
    except subprocess.CalledProcessError:
        pytest.fail("black command is not available")


def test_setup_linting_module_importable():
    """Test that the setup_linting module can be imported."""
    try:
        from code.utils.setup_linting import check_command, install_tool, main
        assert callable(check_command), "check_command should be callable"
        assert callable(install_tool), "install_tool should be callable"
        assert callable(main), "main should be callable"
    except ImportError as e:
        pytest.fail(f"Failed to import setup_linting module: {e}")