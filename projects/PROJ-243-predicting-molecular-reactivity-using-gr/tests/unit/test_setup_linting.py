import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add code to path if not already there
code_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code')
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from setup_linting import (
    check_tool_installed,
    install_tool,
    create_ruff_config,
    create_black_config,
    setup_script_logging
)

def test_check_tool_installed():
    """Test that check_tool_installed returns True for a known package like 'pip'."""
    # 'pip' is always installed in a standard environment
    is_installed, error = check_tool_installed("pip")
    assert is_installed is True
    assert error is None

def test_check_tool_installed_missing():
    """Test that check_tool_installed returns False for a non-existent package."""
    is_installed, error = check_tool_installed("this_package_does_not_exist_12345")
    assert is_installed is False
    assert error is not None
    assert "not installed" in error

def test_create_ruff_config(tmp_path):
    """Test that ruff.toml is created with correct content."""
    # Mock the path to write to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        logger = setup_script_logging()
        path = create_ruff_config(logger)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = f.read()
        
        assert "[lint]" in content
        assert "select" in content
        assert "target-version" in content
    finally:
        os.chdir(original_cwd)

def test_create_black_config(tmp_path):
    """Test that pyproject.toml is updated with Black settings."""
    # Create an empty pyproject.toml first
    pyproject_path = os.path.join(tmp_path, "pyproject.toml")
    with open(pyproject_path, 'w') as f:
        f.write("[project]\nname = 'test'\n")
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        logger = setup_script_logging()
        path = create_black_config(logger)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = f.read()
        
        assert "[tool.black]" in content
        assert "line-length" in content
    finally:
        os.chdir(original_cwd)

def test_create_black_config_appends_if_exists(tmp_path):
    """Test that create_black_config appends if [tool.black] already exists."""
    pyproject_path = os.path.join(tmp_path, "pyproject.toml")
    existing_black = """[project]
name = 'test'

[tool.black]
line-length = 79
"""
    with open(pyproject_path, 'w') as f:
        f.write(existing_black)
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        logger = setup_script_logging()
        path = create_black_config(logger)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = f.read()
        
        # Should not duplicate the section header
        assert content.count("[tool.black]") == 1
        # Should still contain the original line-length
        assert "line-length = 79" in content
    finally:
        os.chdir(original_cwd)