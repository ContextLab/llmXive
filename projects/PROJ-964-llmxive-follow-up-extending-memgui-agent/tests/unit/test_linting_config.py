"""
Unit tests for linting and formatting configuration.
These tests verify that the configuration files exist and are valid.
"""

import os
import json
import yaml
import toml
from pathlib import Path

import pytest

# Get the project root (assuming tests are in tests/unit/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the code directory."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist in code/"

def test_pyproject_toml_valid():
    """Test that pyproject.toml is valid TOML and contains required sections."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert pyproject_path.exists()

    with open(pyproject_path, "r", encoding="utf-8") as f:
        config = toml.load(f)

    # Verify required sections exist
    assert "tool" in config, "pyproject.toml should have 'tool' section"
    assert "ruff" in config["tool"], "pyproject.toml should have [tool.ruff] section"
    assert "black" in config["tool"], "pyproject.toml should have [tool.black] section"
    assert "pytest" in config["tool"], "pyproject.toml should have [tool.pytest.ini_options] section"

def test_ruff_configuration():
    """Test that ruff configuration is properly set."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    with open(pyproject_path, "r", encoding="utf-8") as f:
        config = toml.load(f)

    ruff_config = config["tool"]["ruff"]

    # Check line length
    assert ruff_config.get("line-length") == 88, "Ruff line-length should be 88"

    # Check target version
    assert ruff_config.get("target-version") == "py39", "Ruff target version should be py39"

    # Check that required linters are selected
    assert "E" in ruff_config["select"], "Ruff should select E (pycodestyle errors)"
    assert "F" in ruff_config["select"], "Ruff should select F (Pyflakes)"
    assert "I" in ruff_config["select"], "Ruff should select I (isort)"

def test_black_configuration():
    """Test that black configuration is properly set."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    with open(pyproject_path, "r", encoding="utf-8") as f:
        config = toml.load(f)

    black_config = config["tool"]["black"]

    # Check line length
    assert black_config.get("line-length") == 88, "Black line-length should be 88"

    # Check target versions
    assert "py39" in black_config.get("target-version", []), "Black should target py39"

def test_pre_commit_config_exists():
    """Test that .pre-commit-config.yaml exists in the code directory."""
    pre_commit_path = PROJECT_ROOT / "code" / ".pre-commit-config.yaml"
    assert pre_commit_path.exists(), ".pre-commit-config.yaml should exist in code/"

def test_pre_commit_config_valid():
    """Test that .pre-commit-config.yaml is valid YAML and contains required hooks."""
    pre_commit_path = PROJECT_ROOT / "code" / ".pre-commit-config.yaml"
    assert pre_commit_path.exists()

    with open(pre_commit_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Verify required hooks exist
    assert "repos" in config, ".pre-commit-config.yaml should have 'repos' section"

    hook_repos = [repo["repo"] for repo in config["repos"]]

    # Check for required repositories
    assert any("ruff" in repo for repo in hook_repos), "Should have ruff pre-commit hook"
    assert any("black" in repo for repo in hook_repos), "Should have black pre-commit hook"
    assert any("pre-commit-hooks" in repo for repo in hook_repos), "Should have pre-commit-hooks"

def test_setup_linting_script_exists():
    """Test that setup_linting.sh script exists."""
    setup_script = PROJECT_ROOT / "code" / "scripts" / "setup_linting.sh"
    assert setup_script.exists(), "setup_linting.sh should exist in code/scripts/"

def test_run_linting_script_exists():
    """Test that run_linting.sh script exists."""
    run_script = PROJECT_ROOT / "code" / "scripts" / "run_linting.sh"
    assert run_script.exists(), "run_linting.sh should exist in code/scripts/"

def test_scripts_are_executable():
    """Test that shell scripts have executable permissions."""
    setup_script = PROJECT_ROOT / "code" / "scripts" / "setup_linting.sh"
    run_script = PROJECT_ROOT / "code" / "scripts" / "run_linting.sh"

    assert os.access(setup_script, os.X_OK), "setup_linting.sh should be executable"
    assert os.access(run_script, os.X_OK), "run_linting.sh should be executable"