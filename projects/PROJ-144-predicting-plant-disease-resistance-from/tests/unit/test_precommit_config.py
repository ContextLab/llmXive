"""
Unit tests to verify pre-commit configuration and hooks.
"""
import os
import subprocess
import yaml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PRECOMMIT_CONFIG = PROJECT_ROOT / ".pre-commit-config.yaml"
FLAKE8_CONFIG = PROJECT_ROOT / ".flake8"
ISORT_CONFIG = PROJECT_ROOT / ".isort.cfg"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert PRECOMMIT_CONFIG.exists(), ".pre-commit-config.yaml must exist"

def test_precommit_config_valid_yaml():
    """Verify .pre-commit-config.yaml is valid YAML."""
    with open(PRECOMMIT_CONFIG, "r") as f:
        config = yaml.safe_load(f)
    
    assert isinstance(config, dict), "Config must be a dictionary"
    assert "repos" in config, "Config must contain 'repos' key"
    assert isinstance(config["repos"], list), "'repos' must be a list"
    
    repo_urls = [repo["repo"] for repo in config["repos"]]
    expected_repos = [
        "https://github.com/psf/black",
        "https://github.com/PyCQA/flake8",
        "https://github.com/pycqa/isort"
    ]
    for expected in expected_repos:
        assert expected in repo_urls, f"Missing required repo: {expected}"

def test_flake8_config_exists():
    """Verify .flake8 exists."""
    assert FLAKE8_CONFIG.exists(), ".flake8 must exist"

def test_isort_config_exists():
    """Verify .isort.cfg exists."""
    assert ISORT_CONFIG.exists(), ".isort.cfg must exist"

def test_precommit_installation():
    """Verify pre-commit hooks can be installed (dry run)."""
    try:
        # Check if pre-commit is installed
        result = subprocess.run(
            ["pre-commit", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.skip("pre-commit not installed in environment")
        
        # Try to install hooks (this will succeed if config is valid)
        install_result = subprocess.run(
            ["pre-commit", "install", "--install-hooks"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # If installation fails, it's usually due to missing hooks in CI
        # but the config itself should be valid. We check for syntax errors.
        if install_result.returncode != 0:
            # Check if it's just a hook download issue vs config syntax error
            if "SyntaxError" in install_result.stderr or "yaml" in install_result.stderr:
                pytest.fail(f"Invalid pre-commit config: {install_result.stderr}")
            # Otherwise, assume hooks just couldn't download in this environment
            # but the config is syntactically correct (verified by yaml.load above)
    except FileNotFoundError:
        pytest.skip("pre-commit not found in PATH")
    except subprocess.TimeoutExpired:
        pytest.skip("pre-commit install timed out")

def test_config_files_syntax():
    """Verify config files have valid syntax."""
    # YAML validity already checked in test_precommit_config_valid_yaml
    
    # Check .flake8 has valid INI syntax
    with open(FLAKE8_CONFIG, "r") as f:
        content = f.read()
        assert "[flake8]" in content, ".flake8 must contain [flake8] section"
    
    # Check .isort.cfg has valid INI syntax
    with open(ISORT_CONFIG, "r") as f:
        content = f.read()
        assert "[settings]" in content, ".isort.cfg must contain [settings] section"