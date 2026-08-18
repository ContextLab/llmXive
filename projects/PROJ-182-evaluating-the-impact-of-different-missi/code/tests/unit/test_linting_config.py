"""
Unit tests to verify that linting and formatting configurations are present and valid.

These tests ensure that:
1. pyproject.toml exists and contains [tool.black] and [tool.ruff] sections.
2. .pre-commit-config.yaml exists and references black and ruff.
3. The configuration files are syntactically valid.
"""
import os
import pytest
import tomli
import yaml
from pathlib import Path

# Resolve project root relative to this test file
# Assuming structure: code/tests/unit/test_*.py -> project root is 3 levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_pyproject_toml_has_black_config():
    """Test that pyproject.toml contains [tool.black] configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] section in pyproject.toml"
    
    # Verify expected keys
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing 'line-length' in black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "target-version" in black_config, "Missing 'target-version' in black config"

def test_pyproject_toml_has_ruff_config():
    """Test that pyproject.toml contains [tool.ruff] configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "ruff" in config["tool"], "Missing [tool.ruff] section in pyproject.toml"
    
    # Verify expected keys
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "Missing 'line-length' in ruff config"
    assert "lint" in ruff_config, "Missing [tool.ruff.lint] section"
    assert "select" in ruff_config["lint"], "Missing 'select' in ruff lint config"

def test_pre_commit_config_exists():
    """Test that .pre-commit-config.yaml exists in the project root."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert pre_commit_path.exists(), f".pre-commit-config.yaml not found at {pre_commit_path}"

def test_pre_commit_config_valid_yaml():
    """Test that .pre-commit-config.yaml is valid YAML."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    with open(pre_commit_path, "r") as f:
        try:
            config = yaml.safe_load(f)
            assert config is not None, "YAML file is empty"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in .pre-commit-config.yaml: {e}")

def test_pre_commit_has_black():
    """Test that .pre-commit-config.yaml includes Black hook."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    with open(pre_commit_path, "r") as f:
        config = yaml.safe_load(f)
    
    assert "repos" in config, "Missing 'repos' key in .pre-commit-config.yaml"
    
    black_found = False
    for repo in config["repos"]:
        if "psf/black" in repo.get("repo", ""):
            hooks = repo.get("hooks", [])
            if any(h.get("id") == "black" for h in hooks):
                black_found = True
                break
    
    assert black_found, "Black hook not found in .pre-commit-config.yaml"

def test_pre_commit_has_ruff():
    """Test that .pre-commit-config.yaml includes Ruff hook."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    with open(pre_commit_path, "r") as f:
        config = yaml.safe_load(f)
    
    assert "repos" in config, "Missing 'repos' key in .pre-commit-config.yaml"
    
    ruff_found = False
    for repo in config["repos"]:
        if "astral-sh/ruff-pre-commit" in repo.get("repo", ""):
            hooks = repo.get("hooks", [])
            if any(h.get("id") == "ruff" for h in hooks):
                ruff_found = True
                break
    
    assert ruff_found, "Ruff hook not found in .pre-commit-config.yaml"