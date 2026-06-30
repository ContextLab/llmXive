"""
Tests to verify that linting and formatting configuration files exist and are valid.
"""
import os
import toml
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_ruff_config_exists(project_root):
    """Test that ruff.toml configuration file exists."""
    ruff_config_path = os.path.join(project_root, "ruff.toml")
    assert os.path.exists(ruff_config_path), "ruff.toml configuration file not found"

def test_black_config_exists(project_root):
    """Test that pyproject.toml with Black config exists."""
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    assert os.path.exists(pyproject_path), "pyproject.toml configuration file not found"

def test_black_config_valid(project_root):
    """Test that pyproject.toml contains valid Black configuration."""
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)
    
    assert 'tool' in config, "Missing 'tool' section in pyproject.toml"
    assert 'black' in config['tool'], "Missing 'black' configuration in pyproject.toml"
    assert config['tool']['black'].get('line-length') == 88, "Black line-length should be 88"

def test_ruff_config_valid(project_root):
    """Test that ruff.toml contains valid configuration."""
    ruff_config_path = os.path.join(project_root, "ruff.toml")
    # Basic validation: file should not be empty
    with open(ruff_config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert len(content) > 0, "ruff.toml is empty"
    assert 'line-length' in content, "ruff.toml missing line-length configuration"
    assert 'select' in content, "ruff.toml missing select configuration"