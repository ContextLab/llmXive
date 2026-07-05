"""
Unit tests for linting configuration generation.
"""
import os
import tempfile
import pytest
import sys

# Add code to path if running from tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from lint_config import get_ruff_config, get_black_config, generate_ruff_toml, generate_pyproject_toml

def test_ruff_config_structure():
    """Test that ruff config returns expected keys."""
    config = get_ruff_config()
    assert "lint" in config
    assert "line-length" in config
    assert "target-version" in config
    assert isinstance(config["lint"]["select"], list)
    assert "E" in config["lint"]["select"]
    assert "F" in config["lint"]["select"]

def test_black_config_structure():
    """Test that black config returns expected keys."""
    config = get_black_config()
    assert "line-length" in config
    assert "target-version" in config
    assert config["line-length"] == 88
    assert "py311" in config["target-version"]

def test_generate_ruff_toml(tmp_path):
    """Test generation of ruff.toml file."""
    config_path = generate_ruff_toml(str(tmp_path), "test_ruff.toml")
    assert os.path.exists(config_path)
    
    with open(config_path, "r") as f:
        content = f.read()
    
    assert "line-length = 88" in content
    assert 'target-version = "py311"' in content
    assert "select = [" in content
    assert '"E"' in content

def test_generate_pyproject_toml(tmp_path):
    """Test generation of pyproject.toml black section."""
    config_path = generate_pyproject_toml(str(tmp_path), "test_pyproject.toml")
    assert os.path.exists(config_path)
    
    with open(config_path, "r") as f:
        content = f.read()
    
    assert "[tool.black]" in content
    assert "line-length = 88" in content
    assert "py311" in content