import os
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), ".flake8 configuration file is missing"

def test_black_config_exists():
    """Verify Black is configured in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml is missing"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    precommit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert precommit_path.exists(), ".pre-commit-config.yaml is missing"

def test_requirements_includes_linting_tools():
    """Verify linting tools are listed in requirements or pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    
    # Check for flake8, black, and pre-commit in dependencies
    assert "flake8" in content, "flake8 not found in dependencies"
    assert "black" in content, "black not found in dependencies"
    assert "pre-commit" in content, "pre-commit not found in dependencies"

def test_pyproject_toml_structure():
    """Verify pyproject.toml has required sections."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    
    required_sections = [
        "[build-system]",
        "[project]",
        "[tool.black]",
        "[tool.pytest.ini_options]"
    ]
    
    for section in required_sections:
        assert section in content, f"Required section {section} missing from pyproject.toml"

def test_pre_commit_hooks_valid():
    """Verify pre-commit hooks are configured correctly."""
    precommit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    content = precommit_path.read_text()
    
    required_hooks = ["black", "flake8", "trailing-whitespace"]
    for hook in required_hooks:
        assert hook in content, f"Hook {hook} not configured in .pre-commit-config.yaml"

def test_black_config_settings():
    """Verify Black is configured with 88 line length."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    
    assert "line-length = 88" in content, "Black line-length should be 88"

def test_flake8_config_settings():
    """Verify .flake8 is configured with 88 max line length."""
    flake8_path = PROJECT_ROOT / ".flake8"
    content = flake8_path.read_text()
    
    assert "max-line-length = 88" in content, "flake8 max-line-length should be 88"