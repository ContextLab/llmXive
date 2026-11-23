"""
Tests to verify that linting and formatting configurations are present and valid.
These tests ensure that the project is set up to enforce code quality standards.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    assert (PROJECT_ROOT / "pyproject.toml").exists(), "pyproject.toml is missing"

def test_pyproject_toml_has_black_config():
    """Verify pyproject.toml contains Black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists()
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length" in content, "Black line-length configuration missing"
    assert "target-version" in content, "Black target-version configuration missing"

def test_pyproject_toml_has_ruff_config():
    """Verify pyproject.toml contains Ruff configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists()
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    assert "select" in content, "Ruff select configuration missing"
    assert "ignore" in content, "Ruff ignore configuration missing"

def test_ruff_config_file_exists():
    """Verify .ruff.toml exists as an explicit config file."""
    assert (PROJECT_ROOT / ".ruff.toml").exists(), ".ruff.toml is missing"

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    assert (PROJECT_ROOT / ".flake8").exists(), ".flake8 configuration file is missing"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert (PROJECT_ROOT / ".pre-commit-config.yaml").exists(), ".pre-commit-config.yaml is missing"

def test_pre_commit_has_black_hook():
    """Verify pre-commit config includes Black hook."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert config_path.exists()
    
    content = config_path.read_text()
    assert "black" in content, "Black hook missing in pre-commit config"

def test_pre_commit_has_ruff_hook():
    """Verify pre-commit config includes Ruff hook."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert config_path.exists()
    
    content = config_path.read_text()
    assert "ruff" in content, "Ruff hook missing in pre-commit config"

def test_black_line_length_matches_ruff():
    """Verify Black and Ruff line-length settings are consistent."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    flake8_path = PROJECT_ROOT / ".flake8"
    
    # Check pyproject.toml
    with open(pyproject_path, "r") as f:
        pyproject_content = f.read()
    
    # Check .ruff.toml
    with open(ruff_path, "r") as f:
        ruff_content = f.read()
    
    # Check .flake8
    with open(flake8_path, "r") as f:
        flake8_content = f.read()
    
    # All should use 88 as line length
    assert "line-length = 88" in pyproject_content or 'line-length=88' in pyproject_content
    assert "line-length = 88" in ruff_content or 'line-length=88' in ruff_content
    assert "max-line-length = 88" in flake8_content or 'max-line-length=88' in flake8_content

def test_python_version_target_consistency():
    """Verify Python version target is consistent across tools."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Check for py311 target in both black and ruff sections
    assert "target-version" in content
    assert "py311" in content