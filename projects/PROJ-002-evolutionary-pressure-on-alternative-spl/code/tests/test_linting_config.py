import os
import subprocess
from pathlib import Path
import pytest

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    config_path = Path("code/.flake8")
    assert config_path.exists(), f"Missing flake8 config at {config_path}"
    content = config_path.read_text()
    assert "[flake8]" in content, "Missing [flake8] section in .flake8"

def test_black_config_exists():
    """Verify pyproject.toml contains Black configuration."""
    config_path = Path("code/pyproject.toml")
    assert config_path.exists(), f"Missing pyproject.toml at {config_path}"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists and is valid YAML."""
    config_path = Path("code/.pre-commit-config.yaml")
    assert config_path.exists(), f"Missing .pre-commit-config.yaml at {config_path}"
    # Validate YAML syntax by attempting to parse
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    assert config is not None, "Failed to parse .pre-commit-config.yaml"
    assert "repos" in config, "Missing 'repos' key in .pre-commit-config.yaml"

def test_requirements_includes_linting_tools():
    """Verify linting tools are listed in dependencies."""
    config_path = Path("code/pyproject.toml")
    content = config_path.read_text()
    assert "flake8" in content, "flake8 not found in pyproject.toml dependencies"
    assert "black" in content, "black not found in pyproject.toml dependencies"
    assert "pre-commit" in content, "pre-commit not found in pyproject.toml dependencies"

def test_pyproject_toml_structure():
    """Verify pyproject.toml has required build-system and project sections."""
    config_path = Path("code/pyproject.toml")
    content = config_path.read_text()
    assert "[build-system]" in content, "Missing [build-system] section"
    assert "[project]" in content, "Missing [project] section"
    assert "setuptools" in content, "Missing setuptools in build-system"

def test_pre_commit_hooks_valid():
    """Verify pre-commit hooks reference valid repositories."""
    config_path = Path("code/.pre-commit-config.yaml")
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    repos = config.get("repos", [])
    assert len(repos) >= 3, "Expected at least 3 repos in pre-commit config"
    
    hook_ids = []
    for repo in repos:
        hooks = repo.get("hooks", [])
        for hook in hooks:
            hook_ids.append(hook.get("id"))
    
    assert "black" in hook_ids, "black hook not found"
    assert "flake8" in hook_ids, "flake8 hook not found"

def test_black_config_settings():
    """Verify Black is configured with correct line length."""
    config_path = Path("code/pyproject.toml")
    content = config_path.read_text()
    assert "line-length = 88" in content, "Black line-length should be 88"
    assert 'target-version = ["py311"]' in content, "Black should target Python 3.11"

def test_flake8_config_settings():
    """Verify flake8 is configured with correct settings."""
    config_path = Path("code/.flake8")
    content = config_path.read_text()
    assert "max-line-length = 88" in content, "flake8 max-line-length should be 88"
    assert "E203" in content, "flake8 should ignore E203 (compatible with Black)"
    assert "W503" in content, "flake8 should ignore W503 (compatible with Black)"