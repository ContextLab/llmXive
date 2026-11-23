"""
Unit tests for linting and formatting configuration files.
"""
import os
import json
from pathlib import Path

def test_ruff_toml_exists():
    """Test that ruff.toml file exists."""
    ruff_path = Path("ruff.toml")
    assert ruff_path.exists(), "ruff.toml file does not exist"

def test_pyproject_toml_exists():
    """Test that pyproject.toml file exists."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml file does not exist"

def test_ruff_toml_content():
    """Test that ruff.toml has correct content."""
    ruff_path = Path("ruff.toml")
    content = ruff_path.read_text()
    
    assert "line-length = 88" in content, "ruff.toml missing line-length = 88"
    assert 'target-version = "py39"' in content, "ruff.toml missing target-version = py39"
    assert 'select = ["E", "F", "W", "I"]' in content, "ruff.toml missing select configuration"

def test_pyproject_toml_black_config():
    """Test that pyproject.toml has correct black configuration."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length = 88" in content, "pyproject.toml missing line-length = 88 in black config"
    assert "target-version = ['py39']" in content, "pyproject.toml missing target-version in black config"

def test_configure_linting_script_imports():
    """Test that configure_linting.py can be imported without errors."""
    try:
        from code.configure_linting import (
            ensure_package_installed,
            create_ruff_config,
            create_pyproject_config,
            main
        )
        assert callable(ensure_package_installed)
        assert callable(create_ruff_config)
        assert callable(create_pyproject_config)
        assert callable(main)
    except ImportError as e:
        raise AssertionError(f"Failed to import configure_linting.py: {e}")