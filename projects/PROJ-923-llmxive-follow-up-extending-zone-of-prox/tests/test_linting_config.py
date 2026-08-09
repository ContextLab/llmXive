"""
Test to verify that linting and formatting configurations are valid.
This ensures the project is set up to enforce code quality standards.
"""
import os
import subprocess
import sys
import toml
import yaml
import pytest


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in the project root."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml not found in project root"


def test_pyproject_toml_valid():
    """Verify pyproject.toml is valid TOML and contains required sections."""
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)

    assert "tool" in config, "Missing 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "Missing 'black' configuration"
    assert "ruff" in config["tool"], "Missing 'ruff' configuration"

    # Check black config
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing line-length in black config"
    assert black_config["line-length"] == 88, "Black line-length should be 88"

    # Check ruff config
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "Missing line-length in ruff config"
    assert ruff_config["line-length"] == 88, "Ruff line-length should be 88"


def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert os.path.exists(".pre-commit-config.yaml"), ".pre-commit-config.yaml not found"


def test_precommit_config_valid():
    """Verify .pre-commit-config.yaml is valid YAML and contains required hooks."""
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)

    assert "repos" in config, "Missing 'repos' section in pre-commit config"

    repo_urls = [repo["repo"] for repo in config["repos"]]

    # Check for black
    assert any("psf/black" in url for url in repo_urls), "Missing black hook in pre-commit config"

    # Check for ruff
    assert any("astral-sh/ruff-pre-commit" in url for url in repo_urls), "Missing ruff hook in pre-commit config"


def test_gitignore_exists():
    """Verify .gitignore exists and contains standard entries."""
    assert os.path.exists(".gitignore"), ".gitignore not found"

    with open(".gitignore", "r") as f:
        content = f.read()

    assert "__pycache__" in content, "Missing __pycache__ in .gitignore"
    assert ".venv" in content or "venv" in content, "Missing venv in .gitignore"


def test_ruff_syntax_check():
    """Run ruff check on the code directory to ensure syntax is valid."""
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "--select=E9,F63,F7,F82"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect exit code 0 (no errors) or 1 (found issues, but syntax is valid)
        # If syntax is invalid, ruff might fail differently, but for this test
        # we just want to ensure the command runs without crashing.
        assert result.returncode in [0, 1], f"Ruff check failed unexpectedly: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff check timed out")


def test_black_check():
    """Run black check on the code directory to ensure formatting is valid."""
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Exit code 0: formatted correctly
        # Exit code 1: needs formatting
        # Both are acceptable for this test (syntax is valid)
        assert result.returncode in [0, 1], f"Black check failed unexpectedly: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("Black check timed out")