"""
Tests for linting and formatting configuration.

These tests verify that the configuration files are correctly generated
and contain the expected settings.
"""
import os
import tomli
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.configure_linting import create_ruff_config, create_black_config, create_pre_commit_config

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root for testing."""
    # Change to the temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    # Create necessary directories
    for dir_name in ["data", "results", "state", "code", "tests"]:
        Path(dir_name).mkdir(exist_ok=True)
    
    yield tmp_path
    
    # Restore original directory
    os.chdir(original_cwd)

def test_ruff_config_created(temp_project_root):
    """Test that ruff.toml is created with correct settings."""
    config_path = create_ruff_config()
    
    assert config_path.exists()
    assert config_path.name == "ruff.toml"
    
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    
    assert config["target-version"] == "py311"
    assert config["line-length"] == 88
    assert "E" in config["select"]
    assert "F" in config["select"]
    assert "I" in config["select"]
    assert ".git" in config["exclude"]
    assert "data" in config["exclude"]

def test_black_config_created(temp_project_root):
    """Test that pyproject.toml contains black configuration."""
    config_path = create_black_config()
    
    assert config_path.exists()
    assert config_path.name == "pyproject.toml"
    
    with open(config_path, "r") as f:
        import tomlkit
        doc = tomlkit.parse(f.read())
    
    assert "tool" in doc
    assert "black" in doc["tool"]
    assert doc["tool"]["black"]["line-length"] == 88
    assert "py311" in doc["tool"]["black"]["target-version"]

def test_pre_commit_config_created(temp_project_root):
    """Test that .pre-commit-config.yaml is created with correct hooks."""
    config_path = create_pre_commit_config()
    
    assert config_path.exists()
    assert config_path.name == ".pre-commit-config.yaml"
    
    with open(config_path, "r") as f:
        content = f.read()
    
    assert "ruff" in content
    assert "black" in content
    assert "astral-sh/ruff-pre-commit" in content
    assert "psf/black" in content
    assert "v0.1.6" in content
    assert "23.11.0" in content

def test_all_configs_together(temp_project_root):
    """Test that all configuration files are created correctly together."""
    ruff_config = create_ruff_config()
    black_config = create_black_config()
    pre_commit_config = create_pre_commit_config()
    
    assert ruff_config.exists()
    assert black_config.exists()
    assert pre_commit_config.exists()
    
    # Verify they all have the same base settings
    with open(ruff_config, "rb") as f:
        ruff_data = tomli.load(f)
    
    with open(black_config, "r") as f:
        import tomlkit
        black_data = tomlkit.parse(f.read())
    
    # Both should target Python 3.11
    assert ruff_data["target-version"] == "py311"
    assert "py311" in black_data["tool"]["black"]["target-version"]
    
    # Both should use 88 as line length
    assert ruff_data["line-length"] == 88
    assert black_data["tool"]["black"]["line-length"] == 88