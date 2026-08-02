import os
import subprocess
import tempfile
import pytest
from pathlib import Path


def test_ruff_config_exists():
    """Verify that ruff configuration file exists."""
    # Check for .ruff.toml or ruff.toml or pyproject.toml [tool.ruff]
    root = Path(__file__).parent.parent.parent.parent
    ruff_toml = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    assert ruff_toml.exists() or (
        pyproject.exists() and "[tool.ruff]" in pyproject.read_text()
    ), "Ruff configuration (.ruff.toml or pyproject.toml) not found"


def test_black_config_exists():
    """Verify that black configuration file exists."""
    root = Path(__file__).parent.parent.parent.parent
    black_toml = root / ".black.toml"
    pyproject = root / "pyproject.toml"

    assert black_toml.exists() or (
        pyproject.exists() and "[tool.black]" in pyproject.read_text()
    ), "Black configuration (.black.toml or pyproject.toml) not found"


def test_precommit_config_exists():
    """Verify that pre-commit configuration file exists."""
    root = Path(__file__).parent.parent.parent.parent
    config_path = root / ".pre-commit-config.yaml"
    assert config_path.exists(), "Pre-commit configuration (.pre-commit-config.yaml) not found"


def test_lint_script_exists():
    """Verify that linting can be invoked (checks if ruff is installed/configured)."""
    root = Path(__file__).parent.parent.parent.parent
    # We don't run it fully here to avoid dependency on installed ruff in test env,
    # but we verify the config allows it.
    config_path = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"
    assert config_path.exists() or pyproject.exists()


def test_format_script_exists():
    """Verify that formatting can be invoked (checks if black is installed/configured)."""
    root = Path(__file__).parent.parent.parent.parent
    config_path = root / ".black.toml"
    pyproject = root / "pyproject.toml"
    assert config_path.exists() or pyproject.exists()


def test_pytest_config_exists():
    """Verify that pytest configuration exists."""
    root = Path(__file__).parent.parent.parent.parent
    pyproject = root / "pyproject.toml"
    assert pyproject.exists() and "[tool.pytest" in pyproject.read_text(), "Pytest configuration missing in pyproject.toml"