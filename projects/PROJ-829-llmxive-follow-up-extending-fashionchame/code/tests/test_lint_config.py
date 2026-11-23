"""
Unit tests for linting and formatting configuration.
These tests verify that ruff and black are correctly configured
and can be executed against the codebase.
"""
import subprocess
import sys
from pathlib import Path
import pytest


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def project_root() -> Path:
    return get_project_root()


def test_pyproject_toml_exists(project_root: Path):
    """Test that pyproject.toml exists in the project root."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist in project root"


def test_ruff_check_syntax(project_root: Path):
    """Test that ruff can check syntax without errors (ignoring line length)."""
    ruff_path = project_root / "code"
    try:
        result = subprocess.run(
            ["ruff", "check", str(ruff_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # We expect exit code 0 (no errors) or 1 (found issues but parsed successfully)
        # Exit code 2 would mean a configuration or execution error
        assert result.returncode in (0, 1), (
            f"Ruff check failed with error:\n{result.stderr}"
        )
    except FileNotFoundError:
        pytest.skip("ruff not installed, skipping syntax check")


def test_black_check_syntax(project_root: Path):
    """Test that black can check formatting."""
    black_path = project_root / "code"
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(black_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Exit code 0: all good
        # Exit code 1: formatting issues found (but parsing succeeded)
        # Exit code 2: error
        assert result.returncode in (0, 1), (
            f"Black check failed with error:\n{result.stderr}"
        )
    except FileNotFoundError:
        pytest.skip("black not installed, skipping format check")


def test_ruff_config_loadable(project_root: Path):
    """Test that ruff can load its configuration."""
    config_path = project_root / "pyproject.toml"
    try:
        result = subprocess.run(
            ["ruff", "config", "show"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_root),
        )
        assert result.returncode == 0, (
            f"Ruff config load failed:\n{result.stderr}"
        )
    except FileNotFoundError:
        pytest.skip("ruff not installed, skipping config load test")


def test_black_config_loadable(project_root: Path):
    """Test that black can load its configuration."""
    try:
        result = subprocess.run(
            ["black", "--config", "pyproject.toml", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_root),
        )
        # Black returns 0 on success
        assert result.returncode == 0, (
            f"Black config load failed:\n{result.stderr}"
        )
    except FileNotFoundError:
        pytest.skip("black not installed, skipping config load test")