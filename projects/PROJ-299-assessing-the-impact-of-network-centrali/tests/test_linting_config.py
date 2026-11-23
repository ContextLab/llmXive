"""
Tests to verify linting and formatting configuration is present and valid.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify .ruff.toml exists in the code directory."""
    config_path = PROJECT_ROOT / "code" / ".ruff.toml"
    assert config_path.exists(), "Ruff configuration file (.ruff.toml) is missing."

def test_black_config_in_pyproject():
    """Verify Black settings are present in pyproject.toml."""
    config_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml is missing."

    with open(config_path) as f:
        config = toml.load(f)

    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "black" in config["tool"], "Black configuration missing in pyproject.toml"
    assert config["tool"]["black"].get("line-length") == 88, "Black line-length should be 88"

def test_flake8_config_exists():
    """Verify .flake8 exists in the code directory."""
    config_path = PROJECT_ROOT / "code" / ".flake8"
    assert config_path.exists(), "Flake8 configuration file (.flake8) is missing."

def test_makefile_targets():
    """Verify Makefile contains required lint/format targets."""
    makefile_path = PROJECT_ROOT / "code" / "Makefile"
    assert makefile_path.exists(), "Makefile is missing."

    content = makefile_path.read_text()
    required_targets = ["lint", "format", "format-check", "test"]
    for target in required_targets:
        assert f"{target}:" in content, f"Makefile missing target: {target}"

def test_requirements_dev_includes_linters():
    """Verify requirements-dev.txt includes linter packages."""
    req_path = PROJECT_ROOT / "code" / "requirements-dev.txt"
    assert req_path.exists(), "requirements-dev.txt is missing."

    content = req_path.read_text()
    required_packages = ["ruff", "black", "flake8"]
    for pkg in required_packages:
        assert pkg.lower() in content.lower(), f"Missing package in requirements-dev.txt: {pkg}"
