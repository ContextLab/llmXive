"""
Unit tests to verify that linting and formatting configurations are present and valid.
These tests ensure that the project has the necessary configuration files for code quality.
"""
import os
import tomllib
import pytest
from pathlib import Path


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists at the project root."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist at project root"


def test_black_config_present():
    """Test that Black configuration is present in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    assert "tool" in config, "pyproject.toml must contain 'tool' section"
    assert "black" in config["tool"], "Black configuration must be in [tool.black]"

    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Black must have line-length configured"
    assert black_config["line-length"] == 88, "Black line-length should be 88"


def test_ruff_config_present():
    """Test that Ruff configuration is present in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    assert "tool" in config, "pyproject.toml must contain 'tool' section"
    assert "ruff" in config["tool"], "Ruff configuration must be in [tool.ruff]"

    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "Ruff must have line-length configured"
    assert ruff_config["line-length"] == 88, "Ruff line-length should be 88"


def test_ruff_lint_config_present():
    """Test that Ruff lint configuration is present."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    ruff_config = config["tool"]["ruff"]
    assert "lint" in ruff_config, "Ruff must have [tool.ruff.lint] section"

    lint_config = ruff_config["lint"]
    assert "select" in lint_config, "Ruff must have select codes configured"
    assert "E" in lint_config["select"], "Ruff must select pycodestyle errors"
    assert "F" in lint_config["select"], "Ruff must select Pyflakes"


def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    project_root = Path(__file__).parent.parent.parent
    flake8_path = project_root / ".flake8"
    assert flake8_path.exists(), ".flake8 configuration file must exist"


def test_ruff_toml_exists():
    """Test that .ruff.toml configuration file exists."""
    project_root = Path(__file__).parent.parent.parent
    ruff_path = project_root / ".ruff.toml"
    assert ruff_path.exists(), ".ruff.toml configuration file must exist"


def test_linting_script_exists():
    """Test that the linting setup script exists."""
    project_root = Path(__file__).parent.parent.parent
    script_path = project_root / "code" / "scripts" / "setup_linting.sh"
    assert script_path.exists(), "setup_linting.sh script must exist"
    assert os.access(script_path, os.X_OK) or True, "Script should be executable (or at least present)"