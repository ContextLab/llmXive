import os
import yaml
import pytest
from pathlib import Path

# Import the setup functions to ensure they are callable
# Note: We are testing the configuration file existence and validity primarily
from code.setup_linting import install_dependencies, setup_pre_commit, create_linting_config_files

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_precommit_config_exists():
    """Verify that .pre-commit-config.yaml exists at the project root."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert config_path.exists(), f"File {config_path} does not exist."

def test_precommit_config_valid_yaml():
    """Verify that .pre-commit-config.yaml contains valid YAML."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        assert config is not None, "YAML file is empty or invalid."
        assert "repos" in config, "Config must contain 'repos' key."
        assert isinstance(config["repos"], list), "'repos' must be a list."
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML syntax in .pre-commit-config.yaml: {e}")

def test_precommit_config_has_required_hooks():
    """Verify that the config includes black, flake8, and isort hooks."""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    repos = config.get("repos", [])
    repo_urls = [repo.get("repo") for repo in repos]

    expected_repos = [
        "https://github.com/psf/black",
        "https://github.com/pycqa/flake8",
        "https://github.com/pycqa/isort"
    ]

    for expected in expected_repos:
        assert expected in repo_urls, f"Missing required repo: {expected}"

def test_flake8_config_exists():
    """Verify that .flake8 configuration file exists."""
    config_path = PROJECT_ROOT / ".flake8"
    assert config_path.exists(), f"File {config_path} does not exist."

def test_flake8_config_valid():
    """Verify that .flake8 contains expected settings."""
    config_path = PROJECT_ROOT / ".flake8"
    with open(config_path, "r") as f:
        content = f.read()

    assert "[flake8]" in content, "Missing [flake8] section."
    assert "max-line-length" in content, "Missing max-line-length setting."