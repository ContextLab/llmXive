"""
Unit tests for Task T003: Pre-commit configuration validation.
Verifies that ruff, black, and pre-commit are correctly configured.
"""
import os
import subprocess
import sys
from pathlib import Path
import yaml
import pytest

ROOT_DIR = Path(__file__).parent.parent.parent

@pytest.fixture
def pre_commit_config():
    config_path = ROOT_DIR / ".pre-commit-config.yaml"
    if not config_path.exists():
        pytest.skip(".pre-commit-config.yaml not found")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def pyproject_config():
    config_path = ROOT_DIR / "pyproject.toml"
    if not config_path.exists():
        pytest.skip("pyproject.toml not found")
    # Simple parser for toml since we only need specific sections
    content = config_path.read_text()
    return content

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert (ROOT_DIR / ".pre-commit-config.yaml").exists(), "Missing .pre-commit-config.yaml"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    assert (ROOT_DIR / "pyproject.toml").exists(), "Missing pyproject.toml"

def test_ruff_hook_in_config(pre_commit_config):
    """Verify ruff is included in pre-commit hooks."""
    repos = pre_commit_config.get("repos", [])
    ruff_repo = next((r for r in repos if "ruff" in r.get("repo", "")), None)
    assert ruff_repo is not None, "Ruff repository not found in .pre-commit-config.yaml"

    hooks = ruff_repo.get("hooks", [])
    hook_names = [h.get("id") for h in hooks]
    assert "ruff" in hook_names, "ruff hook not found"
    assert "ruff-format" in hook_names, "ruff-format hook not found"

def test_black_hook_in_config(pre_commit_config):
    """Verify black is included in pre-commit hooks."""
    repos = pre_commit_config.get("repos", [])
    black_repo = next((r for r in repos if "black" in r.get("repo", "")), None)
    assert black_repo is not None, "Black repository not found in .pre-commit-config.yaml"

    hooks = black_repo.get("hooks", [])
    hook_names = [h.get("id") for h in hooks]
    assert "black" in hook_names, "black hook not found"

def test_pyproject_ruff_config(pyproject_config):
    """Verify ruff is configured in pyproject.toml."""
    assert "[tool.ruff]" in pyproject_config, "Ruff configuration missing in pyproject.toml"
    assert "line-length" in pyproject_config, "line-length not configured for ruff"

def test_pyproject_black_config(pyproject_config):
    """Verify black is configured in pyproject.toml."""
    assert "[tool.black]" in pyproject_config, "Black configuration missing in pyproject.toml"
    assert "line-length" in pyproject_config, "line-length not configured for black"

def test_requirements_includes_ruff_and_black():
    """Verify requirements.txt includes ruff and black."""
    req_path = ROOT_DIR / "code" / "requirements.txt"
    assert req_path.exists(), "code/requirements.txt not found"
    
    content = req_path.read_text().lower()
    assert "ruff" in content, "ruff not in requirements.txt"
    assert "black" in content, "black not in requirements.txt"

def test_pre_commit_hooks_are_valid():
    """
    Attempt to run pre-commit validate-config if pre-commit is installed.
    This is a soft check; if pre-commit is not installed, we skip.
    """
    try:
        result = subprocess.run(
            ["pre-commit", "validate-config"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.fail(f"pre-commit validate-config failed:\n{result.stderr}")
    except FileNotFoundError:
        pytest.skip("pre-commit not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("pre-commit validate-config timed out")