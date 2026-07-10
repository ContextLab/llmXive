"""
Test to verify that linting and formatting configurations are present and valid.
This ensures T003 is completed correctly.
"""
import os
import subprocess
import sys
import tomllib
import yaml

import pytest


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at the project root."""
    assert os.path.isfile("pyproject.toml"), "pyproject.toml must exist in project root"


def test_pyproject_contains_black_config():
    """Verify pyproject.toml contains [tool.black] section."""
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    assert "tool" in config, "pyproject.toml must have [tool] section"
    assert "black" in config["tool"], "pyproject.toml must have [tool.black] section"
    assert "line-length" in config["tool"]["black"], "Black config must specify line-length"


def test_pyproject_contains_ruff_config():
    """Verify pyproject.toml contains [tool.ruff] section."""
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    assert "tool" in config, "pyproject.toml must have [tool] section"
    assert "ruff" in config["tool"], "pyproject.toml must have [tool.ruff] section"
    assert "lint" in config["tool"]["ruff"], "Ruff config must have [tool.ruff.lint] section"
    assert "select" in config["tool"]["ruff"]["lint"], "Ruff must specify lint rules to select"


def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert os.path.isfile(".pre-commit-config.yaml"), ".pre-commit-config.yaml must exist"


def test_precommit_config_valid_yaml():
    """Verify .pre-commit-config.yaml is valid YAML."""
    with open(".pre-commit-config.yaml", "r") as f:
        try:
            config = yaml.safe_load(f)
            assert "repos" in config, ".pre-commit-config.yaml must have 'repos' key"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")


def test_precommit_config_includes_ruff():
    """Verify pre-commit config includes ruff."""
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)
    repos = config.get("repos", [])
    ruff_found = any("ruff" in str(repo.get("repo", "")) for repo in repos)
    assert ruff_found, "pre-commit config must include ruff repository"


def test_precommit_config_includes_black():
    """Verify pre-commit config includes black."""
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)
    repos = config.get("repos", [])
    black_found = any("black" in str(repo.get("repo", "")) for repo in repos)
    assert black_found, "pre-commit config must include black repository"


def test_requirements_includes_linting_tools():
    """Verify requirements.txt includes ruff and black."""
    assert os.path.isfile("requirements.txt"), "requirements.txt must exist"
    with open("requirements.txt", "r") as f:
        content = f.read().lower()
    assert "ruff" in content, "requirements.txt must include ruff"
    assert "black" in content, "requirements.txt must include black"