"""
Unit tests for linting and formatting configuration.
Verifies that ruff and black are configured correctly.
"""
import os
import sys
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist in project root"

def test_pyproject_has_black_config():
    """Test that pyproject.toml contains Black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    assert "tool" in config, "pyproject.toml must contain 'tool' section"
    assert "black" in config["tool"], "pyproject.toml must contain [tool.black] section"
    assert "line-length" in config["tool"]["black"], "Black config must have line-length"
    assert config["tool"]["black"]["line-length"] == 100, "Black line-length must be 100"

def test_pyproject_has_ruff_config():
    """Test that pyproject.toml contains Ruff configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    assert "tool" in config, "pyproject.toml must contain 'tool' section"
    assert "ruff" in config["tool"], "pyproject.toml must contain [tool.ruff] section"
    assert "line-length" in config["tool"]["ruff"], "Ruff config must have line-length"
    assert config["tool"]["ruff"]["line-length"] == 100, "Ruff line-length must be 100"
    assert "select" in config["tool"]["ruff"], "Ruff config must have select rules"

def test_ruff_config_file_exists():
    """Test that .ruff.toml exists as a standalone config."""
    ruff_config = PROJECT_ROOT / ".ruff.toml"
    assert ruff_config.exists(), ".ruff.toml must exist in project root"

def test_black_config_file_exists():
    """Test that .black.toml exists as a standalone config."""
    black_config = PROJECT_ROOT / ".black.toml"
    assert black_config.exists(), ".black.toml must exist in project root"

def test_lint_check_script_exists():
    """Test that code/lint_check.py exists."""
    lint_script = PROJECT_ROOT / "code" / "lint_check.py"
    assert lint_script.exists(), "code/lint_check.py must exist"

def test_lint_check_script_is_valid_python():
    """Test that code/lint_check.py is valid Python."""
    lint_script = PROJECT_ROOT / "code" / "lint_check.py"
    try:
        with open(lint_script, "r") as f:
            compile(f.read(), lint_script, "exec")
    except SyntaxError as e:
        pytest.fail(f"lint_check.py has syntax errors: {e}")

def test_ruff_dependencies_included():
    """Test that ruff and black are in dependencies."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    deps = config.get("project", {}).get("dependencies", [])
    dev_deps = config.get("project", {}).get("optional-dependencies", {}).get("dev", [])

    all_deps = deps + dev_deps
    assert any("ruff" in dep for dep in all_deps), "ruff must be in dependencies"
    assert any("black" in dep for dep in all_deps), "black must be in dependencies"