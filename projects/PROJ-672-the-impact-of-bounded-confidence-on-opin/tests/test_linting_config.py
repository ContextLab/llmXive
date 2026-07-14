"""
Test to verify that linting configuration files exist and are valid.
This task (T003) requires flake8 and black configuration.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent / "code"

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), f"Missing .flake8 config at {flake8_path}"

def test_pyproject_black_config_exists():
    """Verify pyproject.toml exists and contains black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"Missing pyproject.toml at {pyproject_path}"

    with open(pyproject_path, "r") as f:
        config = toml.load(f)

    assert "tool" in config, "Missing 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "Missing 'black' configuration in pyproject.toml"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing 'line-length' in black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert pre_commit_path.exists(), f"Missing .pre-commit-config.yaml at {pre_commit_path}"

    with open(pre_commit_path, "r") as f:
        content = f.read()
        assert "black" in content, "pre-commit config must include black hook"
        assert "flake8" in content, "pre-commit config must include flake8 hook"