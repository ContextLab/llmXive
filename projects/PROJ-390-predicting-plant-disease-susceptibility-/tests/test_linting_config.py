import os
import pytest
from pathlib import Path
import toml
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_ruff_config_exists():
    """Verify .ruff.toml exists and is valid TOML."""
    path = PROJECT_ROOT / ".ruff.toml"
    assert path.exists(), "Missing .ruff.toml"
    # Validate it's parseable TOML
    with open(path, "r") as f:
        config = toml.load(f)
    assert "lint" in config or "format" in config, ".ruff.toml must contain lint or format sections"

def test_flake8_config_exists():
    """Verify .flake8 exists and is valid INI."""
    path = PROJECT_ROOT / ".flake8"
    assert path.exists(), "Missing .flake8"
    # Basic check for content
    with open(path, "r") as f:
        content = f.read()
    assert "[flake8]" in content, ".flake8 must contain [flake8] section"

def test_pyproject_toml_has_black_settings():
    """Verify pyproject.toml contains Black settings."""
    path = PROJECT_ROOT / "pyproject.toml"
    assert path.exists(), "Missing pyproject.toml"
    with open(path, "r") as f:
        config = toml.load(f)
    assert "tool" in config, "pyproject.toml must contain [tool] section"
    assert "black" in config["tool"], "pyproject.toml must contain [tool.black]"
    assert "line-length" in config["tool"]["black"], "[tool.black] must define line-length"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists and hooks are defined."""
    path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert path.exists(), "Missing .pre-commit-config.yaml"
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    assert "repos" in config, "Must define repos"
    hook_ids = []
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            hook_ids.append(hook["id"])
    assert "ruff" in hook_ids or "ruff-format" in hook_ids, "Must include ruff hook"
    assert "black" in hook_ids, "Must include black hook"
    assert "flake8" in hook_ids, "Must include flake8 hook"