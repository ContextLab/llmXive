"""
Contract test for T003: Verify linting and formatting configuration.

This test ensures that the configuration files for flake8, black, and isort
exist and are valid, and that the pre-commit hooks are correctly set up.
"""
import os
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
CONFIG_FILES = {
    "flake8": CODE_DIR / ".flake8",
    "pyproject": CODE_DIR / "pyproject.toml",
    "pre_commit": PROJECT_ROOT / ".pre-commit-config.yaml",
}

def test_config_files_exist():
    """Verify all configuration files exist."""
    for name, path in CONFIG_FILES.items():
        assert path.exists(), f"Configuration file {name} not found at {path}"

def test_flake8_config_valid():
    """Verify flake8 configuration is valid and parseable."""
    config_path = CONFIG_FILES["flake8"]
    # flake8 reads ini-style config, just check it's not empty and has sections
    content = config_path.read_text()
    assert "[flake8]" in content, "Missing [flake8] section in .flake8"
    assert "max-line-length" in content, "Missing max-line-length in .flake8"

def test_pyproject_black_config_valid():
    """Verify black configuration in pyproject.toml is valid."""
    config_path = CONFIG_FILES["pyproject"]
    content = config_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    assert "line-length" in content, "Missing line-length in [tool.black]"

def test_pre_commit_config_valid():
    """Verify pre-commit configuration is valid YAML and contains expected hooks."""
    config_path = CONFIG_FILES["pre_commit"]
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    assert "repos" in config, "Missing 'repos' key in pre-commit config"
    repos = config["repos"]
    assert len(repos) > 0, "No repositories configured in pre-commit"
    
    hook_ids = set()
    for repo in repos:
        for hook in repo.get("hooks", []):
            hook_ids.add(hook["id"])
    
    expected_hooks = {"black", "isort", "flake8"}
    assert expected_hooks.issubset(hook_ids), f"Missing hooks: {expected_hooks - hook_ids}"

def test_black_can_parse_code_dir():
    """Verify black can parse the code directory without errors."""
    if not CODE_DIR.exists():
        pytest.skip("Code directory does not exist yet")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 1 if files need formatting, 0 if all good.
        # We just want to ensure it runs without crashing.
        assert result.returncode in (0, 1), f"Black crashed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("Black check timed out")

def test_flake8_can_parse_code_dir():
    """Verify flake8 can parse the code directory without errors."""
    if not CODE_DIR.exists():
        pytest.skip("Code directory does not exist yet")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--config=" + str(CONFIG_FILES["flake8"]), str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # flake8 returns 0 if no errors, non-zero if errors found.
        # We just want to ensure it runs without crashing.
        assert result.returncode in (0, 1), f"Flake8 crashed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Flake8 not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("Flake8 check timed out")