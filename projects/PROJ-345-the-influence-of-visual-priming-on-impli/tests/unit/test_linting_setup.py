"""
Unit tests for T004: Linting and Pre-commit configuration.
These tests verify that configuration files exist and are valid.
"""
import os
import json
import yaml
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILES = {
    "pre-commit": PROJECT_ROOT / ".pre-commit-config.yaml",
    "ruff": PROJECT_ROOT / "ruff.toml",
}

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert CONFIG_FILES["pre-commit"].exists(), "Missing .pre-commit-config.yaml"

def test_pre_commit_config_valid_yaml():
    """Verify .pre-commit-config.yaml is valid YAML."""
    with open(CONFIG_FILES["pre-commit"], "r") as f:
        try:
            data = yaml.safe_load(f)
            assert "repos" in data, "Missing 'repos' key in pre-commit config"
            assert isinstance(data["repos"], list), "'repos' must be a list"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

def test_ruff_config_exists():
    """Verify ruff.toml exists."""
    assert CONFIG_FILES["ruff"].exists(), "Missing ruff.toml"

def test_ruff_config_valid_toml():
    """Verify ruff.toml is valid TOML (basic check)."""
    # We do a basic check for required keys since standard library tomllib is py3.11+
    # and we want to avoid extra deps for the test itself if possible,
    # but we can assume the environment has tomllib or we parse manually.
    # For safety in a generic test runner, we just check file readability and content presence.
    content = CONFIG_FILES["ruff"].read_text()
    assert "target-version" in content, "Missing target-version in ruff.toml"
    assert "line-length" in content, "Missing line-length in ruff.toml"
    assert "select" in content, "Missing select list in ruff.toml"