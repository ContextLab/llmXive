"""
Contract tests for linting and formatting configuration files.
Verifies that .flake8, pyproject.toml, and .editorconfig exist and contain required settings.
"""
import os
import configparser
import tomllib
from pathlib import Path

import pytest


def test_flake8_exists_and_configured():
    """Verify .flake8 exists with max-line-length=88 and exclude=venv."""
    flake8_path = Path(".flake8")
    assert flake8_path.exists(), ".flake8 file must exist at project root"

    config = configparser.ConfigParser()
    config.read(flake8_path)

    assert "flake8" in config, "Must have [flake8] section"
    assert config["flake8"].get("max-line-length") == "88", "max-line-length must be 88"
    assert "venv" in config["flake8"].get("exclude", ""), "exclude must include venv"


def test_pyproject_toml_black_config():
    """Verify pyproject.toml exists with black target-version=py311."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml file must exist at project root"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    assert "tool" in data, "Must have [tool] section"
    assert "black" in data["tool"], "Must have [tool.black] section"
    assert "target-version" in data["tool"]["black"], "Must have target-version in black config"
    
    target_versions = data["tool"]["black"]["target-version"]
    assert "py311" in target_versions, "target-version must include py311"


def test_editorconfig_exists_and_configured():
    """Verify .editorconfig exists with indent_size=4 and end_of_line=lf."""
    editorconfig_path = Path(".editorconfig")
    assert editorconfig_path.exists(), ".editorconfig file must exist at project root"

    content = editorconfig_path.read_text()
    
    assert "indent_size = 4" in content, "Must have indent_size = 4"
    assert "end_of_line = lf" in content, "Must have end_of_line = lf"
    assert "root = true" in content, "Must have root = true"