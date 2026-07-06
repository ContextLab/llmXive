"""
Tests to verify that linting configuration files exist and are valid.
"""
import os
import yaml
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    config_path = ROOT / ".flake8"
    assert config_path.exists(), ".flake8 file is missing"
    
    # Basic validation: ensure it's not empty
    assert config_path.stat().st_size > 0, ".flake8 file is empty"

def test_isort_config_exists():
    """Verify .isort.cfg configuration file exists."""
    config_path = ROOT / ".isort.cfg"
    assert config_path.exists(), ".isort.cfg file is missing"
    assert config_path.stat().st_size > 0, ".isort.cfg file is empty"

def test_precommit_config_valid_yaml():
    """Verify .pre-commit-config.yaml is valid YAML and contains expected repos."""
    config_path = ROOT / ".pre-commit-config.yaml"
    assert config_path.exists(), ".pre-commit-config.yaml is missing"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert 'repos' in config, "Missing 'repos' key in .pre-commit-config.yaml"
    assert isinstance(config['repos'], list), "'repos' must be a list"
    
    repo_ids = [repo['repo'] for repo in config['repos']]
    expected_repos = [
        "https://github.com/pre-commit/pre-commit-hooks",
        "https://github.com/psf/black",
        "https://github.com/pycqa/isort",
        "https://github.com/pycqa/flake8"
    ]
    
    for expected in expected_repos:
        assert expected in repo_ids, f"Missing repo {expected} in pre-commit config"

def test_requirements_contains_linting_tools():
    """Verify requirements.txt contains linting dependencies."""
    req_path = ROOT / "requirements.txt"
    assert req_path.exists(), "requirements.txt is missing"
    
    content = req_path.read_text()
    required_packages = ["black", "flake8", "isort", "pre-commit"]
    
    for pkg in required_packages:
        assert pkg.lower() in content.lower(), f"Missing {pkg} in requirements.txt"
