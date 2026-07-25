"""
Tests to verify linting and formatting configuration files exist and are valid.
These tests ensure T003 (Configure linting) has been satisfied.
"""
import os
import subprocess
import tomli
import pytest


def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    assert os.path.exists(".flake8"), "Missing .flake8 configuration file"


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    assert os.path.exists("pyproject.toml"), "Missing pyproject.toml configuration file"


def test_pyproject_black_config():
    """Verify Black configuration exists in pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] section"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing line-length in Black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"


def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert os.path.exists(".pre-commit-config.yaml"), "Missing .pre-commit-config.yaml"


def test_pre_commit_hooks_valid():
    """Verify pre-commit configuration is valid YAML and contains expected hooks."""
    import yaml

    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)

    assert "repos" in config, "Missing 'repos' in pre-commit config"

    hook_repos = [repo["repo"] for repo in config["repos"]]
    assert any("black" in repo for repo in hook_repos), "Missing Black hook in pre-commit config"
    assert any("flake8" in repo for repo in hook_repos), "Missing Flake8 hook in pre-commit config"


def test_flake8_syntax_check():
    """Run flake8 on a minimal syntax check to ensure it is installed and configured."""
    # Create a temporary minimal python file to test
    test_file = "tests/_temp_syntax_check.py"
    with open(test_file, "w") as f:
        f.write("x = 1\n")

    try:
        result = subprocess.run(
            ["flake8", test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        # flake8 returns 0 if no issues, or non-zero if issues found.
        # We just want to ensure it runs without crashing.
        assert result.returncode in [0, 1], f"Flake8 crashed: {result.stderr}"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)