"""
Contract tests for linting and formatting configuration.
Ensures that flake8, black, and pre-commit are correctly configured.
"""
import os
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    config_path = PROJECT_ROOT / ".flake8"
    assert config_path.exists(), ".flake8 configuration file not found"

def test_black_config_exists():
    """Verify Black is configured in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml not found"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"
    assert "line-length = 88" in content, "Black line-length not set to 88"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists and is valid YAML."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert config_path.exists(), ".pre-commit-config.yaml not found"
    # Basic YAML validity check by attempting to parse
    try:
        import yaml
        with open(config_path) as f:
            yaml.safe_load(f)
    except ImportError:
        # If yaml is not installed, skip parsing but pass existence check
        pass
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

def test_requirements_includes_linting_tools():
    """Verify requirements.txt or pyproject.toml includes linting dependencies."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    content = pyproject_path.read_text()
    
    # Check for linting dependencies in pyproject.toml
    required_tools = ["flake8", "black", "isort", "pre-commit"]
    for tool in required_tools:
        assert tool.lower() in content.lower(), f"Linting tool {tool} not found in dependencies"

def test_pyproject_toml_structure():
    """Verify pyproject.toml has correct structure for build system and tools."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    content = config_path.read_text()
    
    assert "[build-system]" in content, "Missing [build-system] section"
    assert "[tool.black]" in content, "Missing [tool.black] section"
    assert "[tool.isort]" in content, "Missing [tool.isort] section"
    assert "[tool.pytest.ini_options]" in content, "Missing pytest configuration"

def test_pre_commit_hooks_valid():
    """Verify pre-commit hooks are configured for black and flake8."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    content = config_path.read_text()
    
    assert "black" in content, "Black hook not found in pre-commit config"
    assert "flake8" in content, "flake8 hook not found in pre-commit config"

def test_black_config_settings():
    """Verify Black has correct configuration settings."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    content = config_path.read_text()
    
    assert "line-length = 88" in content, "Black line-length should be 88"
    assert "target-version" in content, "Black target-version not configured"

def test_flake8_config_settings():
    """Verify flake8 has correct configuration settings."""
    config_path = PROJECT_ROOT / ".flake8"
    content = config_path.read_text()
    
    assert "max-line-length" in content, "flake8 max-line-length not configured"
    assert "E203" in content or "extend-ignore" in content, "flake8 should ignore E203 for Black compatibility"