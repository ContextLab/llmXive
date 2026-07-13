"""
Unit tests for linting and formatting configuration.
"""
import subprocess
import sys
from pathlib import Path
import pytest

def test_ruff_installed():
    """Test that ruff is installed."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "ruff" in result.stdout.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("ruff is not installed")

def test_black_installed():
    """Test that black is installed."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        assert "black" in result.stdout.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("black is not installed")

def test_pyproject_has_ruff_config():
    """Test that pyproject.toml contains ruff configuration."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml not found"
    
    with open(pyproject, 'r') as f:
        content = f.read()
    
    assert "[tool.ruff]" in content, "Ruff configuration missing from pyproject.toml"

def test_pyproject_has_black_config():
    """Test that pyproject.toml contains black configuration."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml not found"
    
    with open(pyproject, 'r') as f:
        content = f.read()
    
    assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

def test_precommit_config_exists():
    """Test that .pre-commit-config.yaml exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    precommit = project_root / ".pre-commit-config.yaml"
    
    assert precommit.exists(), ".pre-commit-config.yaml not found"
    
    with open(precommit, 'r') as f:
        content = f.read()
    
    assert "ruff" in content, "ruff not configured in pre-commit"
    assert "black" in content, "black not configured in pre-commit"
