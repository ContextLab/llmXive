"""
Tests to verify linting and formatting configuration (Task T003).
These tests ensure pyproject.toml and .pre-commit-config.yaml are correctly set up.
"""
import os
import tomli
import yaml
import pytest
from pathlib import Path

# Get the project root (assuming tests are in code/tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture
def pyproject_config():
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist"
    with open(pyproject_path, "rb") as f:
        return tomli.load(f)

@pytest.fixture
def pre_commit_config():
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert pre_commit_path.exists(), ".pre-commit-config.yaml must exist"
    with open(pre_commit_path, "r") as f:
        return yaml.safe_load(f)

def test_black_config_exists(pyproject_config):
    """Verify Black is configured in pyproject.toml."""
    assert "tool" in pyproject_config
    assert "black" in pyproject_config["tool"]
    assert "line-length" in pyproject_config["tool"]["black"]
    assert pyproject_config["tool"]["black"]["line-length"] == 88

def test_ruff_config_exists(pyproject_config):
    """Verify Ruff is configured in pyproject.toml."""
    assert "tool" in pyproject_config
    assert "ruff" in pyproject_config["tool"]
    assert "line-length" in pyproject_config["tool"]["ruff"]
    assert pyproject_config["tool"]["ruff"]["line-length"] == 88

def test_ruff_lint_rules_selected(pyproject_config):
    """Verify Ruff has lint rules selected."""
    assert "lint" in pyproject_config["tool"]["ruff"]
    assert "select" in pyproject_config["tool"]["ruff"]["lint"]
    rules = pyproject_config["tool"]["ruff"]["lint"]["select"]
    # Check for essential rule groups
    assert "E" in rules  # pycodestyle errors
    assert "F" in rules  # pyflakes
    assert "I" in rules  # isort

def test_dev_dependencies_include_linters(pyproject_config):
    """Verify dev dependencies include ruff and black."""
    deps = pyproject_config.get("project", {}).get("optional-dependencies", {})
    assert "dev" in deps
    dev_deps = deps["dev"]
    has_ruff = any("ruff" in dep for dep in dev_deps)
    has_black = any("black" in dep for dep in dev_deps)
    assert has_ruff, "dev dependencies must include ruff"
    assert has_black, "dev dependencies must include black"

def test_pre_commit_hooks_configured(pre_commit_config):
    """Verify pre-commit hooks for black and ruff are configured."""
    assert "repos" in pre_commit_config
    repos = pre_commit_config["repos"]
    
    has_ruff = False
    has_black = False
    
    for repo in repos:
        if "ruff-pre-commit" in repo.get("repo", ""):
            hooks = repo.get("hooks", [])
            has_ruff = any(h.get("id") in ["ruff", "ruff-format"] for h in hooks)
        if "psf/black" in repo.get("repo", ""):
            hooks = repo.get("hooks", [])
            has_black = any(h.get("id") == "black" for h in hooks)
    
    assert has_ruff, "pre-commit must configure ruff"
    assert has_black, "pre-commit must configure black"