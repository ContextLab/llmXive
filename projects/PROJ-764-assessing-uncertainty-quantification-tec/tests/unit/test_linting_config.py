"""
Unit tests to verify that linting and formatting configurations are present and valid.
"""
import os
import yaml
import toml
import pytest
from pathlib import Path

# Get the project root directory (assuming tests are in tests/unit/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_pyproject_toml_valid_black_config():
    """Test that pyproject.toml contains valid black configuration."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "black" in config["tool"], "black configuration missing in pyproject.toml"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "line-length not configured for black"
    assert black_config["line-length"] == 88, "black line-length should be 88"

def test_pyproject_toml_valid_ruff_config():
    """Test that pyproject.toml contains valid ruff configuration."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "ruff" in config["tool"], "ruff configuration missing in pyproject.toml"

    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "line-length not configured for ruff"
    assert ruff_config["line-length"] == 88, "ruff line-length should be 88"
    assert "select" in ruff_config, "select rules not configured for ruff"

def test_precommit_config_exists():
    """Test that .pre-commit-config.yaml exists."""
    precommit_path = PROJECT_ROOT / "code" / ".pre-commit-config.yaml"
    assert precommit_path.exists(), f".pre-commit-config.yaml not found at {precommit_path}"

def test_precommit_config_valid():
    """Test that .pre-commit-config.yaml is valid YAML and contains black and ruff."""
    precommit_path = PROJECT_ROOT / "code" / ".pre-commit-config.yaml"
    with open(precommit_path, "r") as f:
        config = yaml.safe_load(f)

    assert "repos" in config, "repos section missing in .pre-commit-config.yaml"

    repos = config["repos"]
    repo_urls = [repo["repo"] for repo in repos]

    assert any("black" in url for url in repo_urls), "black not configured in pre-commit"
    assert any("ruff" in url for url in repo_urls), "ruff not configured in pre-commit"
