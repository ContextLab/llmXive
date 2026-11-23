"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import yaml
import toml
import pytest


@pytest.mark.linting
def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml not found at project root"


@pytest.mark.linting
def test_pyproject_toml_black_config():
    """Verify pyproject.toml contains valid Black configuration."""
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] section"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing line-length in Black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "target-version" in black_config, "Missing target-version in Black config"


@pytest.mark.linting
def test_pyproject_toml_ruff_config():
    """Verify pyproject.toml contains valid Ruff configuration."""
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "ruff" in config["tool"], "Missing [tool.ruff] section"
    
    ruff_config = config["tool"]["ruff"]
    assert "select" in ruff_config, "Missing select rules in Ruff config"
    assert "ignore" in ruff_config, "Missing ignore rules in Ruff config"


@pytest.mark.linting
def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists at project root."""
    assert os.path.exists(".pre-commit-config.yaml"), ".pre-commit-config.yaml not found"


@pytest.mark.linting
def test_precommit_config_valid_yaml():
    """Verify .pre-commit-config.yaml is valid YAML and contains required hooks."""
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    assert "repos" in config, "Missing 'repos' key in .pre-commit-config.yaml"
    assert isinstance(config["repos"], list), "'repos' should be a list"
    
    # Check for required hooks
    repo_urls = [repo.get("repo", "") for repo in config["repos"]]
    
    required_repos = [
        "https://github.com/pre-commit/pre-commit-hooks",
        "https://github.com/astral-sh/ruff-pre-commit",
        "https://github.com/psf/black",
    ]
    
    for required in required_repos:
        assert any(required in url for url in repo_urls), f"Missing required repo: {required}"


@pytest.mark.linting
def test_setup_linting_script_exists():
    """Verify setup script exists and is executable."""
    assert os.path.exists("scripts/setup_linting.sh"), "setup_linting.sh not found"
    
    # Check if it's executable (on Unix systems)
    if os.name != "nt":
        assert os.access("scripts/setup_linting.sh", os.X_OK), "setup_linting.sh is not executable"