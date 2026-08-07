"""
Unit tests for linting and formatting configuration.
"""
import os
import pytest
from pathlib import Path
import yaml

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent.parent

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the project root."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist in project root"

def test_black_section_exists():
    """Test that [tool.black] section exists in pyproject.toml."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml should contain [tool.black] section"

def test_ruff_section_exists():
    """Test that [tool.ruff] section exists in pyproject.toml."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml should contain [tool.ruff] section"

def test_black_line_length():
    """Test that black line-length is configured."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    with open(pyproject_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert "tool" in config, "pyproject.toml should have [tool] section"
    assert "black" in config["tool"], "pyproject.toml should have [tool.black] section"
    assert "line-length" in config["tool"]["black"], "black should have line-length configured"
    
    # Default should be 100 based on our config
    assert config["tool"]["black"]["line-length"] == 100, "black line-length should be 100"

def test_ruff_line_length():
    """Test that ruff line-length is configured."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    with open(pyproject_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert "tool" in config, "pyproject.toml should have [tool] section"
    assert "ruff" in config["tool"], "pyproject.toml should have [tool.ruff] section"
    assert "line-length" in config["tool"]["ruff"], "ruff should have line-length configured"
    
    # Default should be 100 based on our config
    assert config["tool"]["ruff"]["line-length"] == 100, "ruff line-length should be 100"

def test_ruff_select_rules():
    """Test that ruff has select rules configured."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    with open(pyproject_path, 'r') as f:
        config = yaml.safe_load(f)
    
    ruff_config = config["tool"]["ruff"]
    assert "select" in ruff_config, "ruff should have select rules configured"
    
    # Check for common rules
    required_rules = ["E", "W", "F"]
    for rule in required_rules:
        assert rule in ruff_config["select"], f"ruff should select rule {rule}"

def test_pytest_config_exists():
    """Test that pytest configuration exists."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    with open(pyproject_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert "tool" in config, "pyproject.toml should have [tool] section"
    assert "pytest" in config["tool"], "pyproject.toml should have [tool.pytest.ini_options] section"
    
    pytest_config = config["tool"]["pytest"]["ini_options"]
    assert "testpaths" in pytest_config, "pytest should have testpaths configured"
    assert "tests" in pytest_config["testpaths"], "pytest testpaths should include 'tests'"