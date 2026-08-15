"""
Tests to verify that linting and formatting configurations are present and valid.
These tests ensure that the project has the required tooling setup for T003.
"""
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), "flake8 configuration (.flake8) not found"
    assert flake8_path.stat().st_size > 0, "flake8 configuration is empty"

def test_black_config_exists():
    """Verify black configuration exists (in pyproject.toml)."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"

def test_pre_commit_config_exists():
    """Verify pre-commit configuration file exists."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert pre_commit_path.exists(), "pre-commit configuration (.pre-commit-config.yaml) not found"
    
    content = pre_commit_path.read_text()
    assert "black" in content, "Black hook not found in pre-commit config"
    assert "flake8" in content, "flake8 hook not found in pre-commit config"

def test_requirements_includes_linting_tools():
    """Verify that linting tools are listed in requirements.txt."""
    requirements_path = PROJECT_ROOT / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt not found"
    
    content = requirements_path.read_text()
    assert "flake8" in content, "flake8 not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"

def test_pyproject_toml_structure():
    """Verify pyproject.toml has required sections."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    assert "[build-system]" in content, "build-system section missing"
    assert "[tool.black]" in content, "Black tool configuration missing"
    assert "[tool.isort]" in content, "isort tool configuration missing"
    assert "[tool.pytest.ini_options]" in content, "pytest configuration missing"

@pytest.mark.skipif(
    not os.path.exists(str(PROJECT_ROOT / ".pre-commit-config.yaml")),
    reason="pre-commit not initialized"
)
def test_pre_commit_hooks_valid():
    """Validate pre-commit hooks configuration syntax."""
    import yaml
    
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert isinstance(config, dict), "Invalid YAML structure"
        assert "repos" in config, "repos key missing in pre-commit config"
        assert len(config["repos"]) > 0, "No repositories configured"
        
        # Check for required hooks
        hook_names = set()
        for repo in config["repos"]:
            for hook in repo.get("hooks", []):
                hook_names.add(hook["id"])
        
        assert "black" in hook_names, "Black hook not configured"
        assert "flake8" in hook_names, "flake8 hook not configured"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

def test_black_config_settings():
    """Verify black configuration settings match project standards."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    
    # Check line length
    assert "line-length = 88" in content, "Black line-length should be 88"
    
    # Check target version
    assert "py311" in content, "Black should target Python 3.11"

def test_flake8_config_settings():
    """Verify flake8 configuration settings."""
    flake8_path = PROJECT_ROOT / ".flake8"
    content = flake8_path.read_text()
    
    assert "max-line-length = 88" in content, "flake8 max-line-length should be 88"
    assert "E203" in content, "flake8 should ignore E203 (compatible with Black)"
    assert "W503" in content, "flake8 should ignore W503 (compatible with Black)"