"""
Unit tests to verify linting and formatting configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def test_pyproject_toml_exists() -> None:
    """Test that pyproject.toml exists in the project root."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"


def test_black_config_present() -> None:
    """Test that black configuration is present in pyproject.toml."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"
    assert "line-length" in content, "line-length configuration for black not found"
    assert "target-version" in content, "target-version configuration for black not found"


def test_ruff_config_present() -> None:
    """Test that ruff configuration is present in pyproject.toml."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration section not found in pyproject.toml"
    assert "[tool.ruff.lint]" in content, "Ruff lint configuration section not found in pyproject.toml"


def test_ruff_is_installed() -> None:
    """Test that ruff is installed and runnable."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("ruff is not installed or not in PATH")


def test_black_is_installed() -> None:
    """Test that black is installed and runnable."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("black is not installed or not in PATH")