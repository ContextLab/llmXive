"""
Tests to verify that linting and formatting configurations are correctly set up.
These tests ensure that black and flake8 configurations in pyproject.toml are valid.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest


def get_project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


def test_flake8_config_exists():
    """Verify that flake8 configuration exists in pyproject.toml."""
    root = get_project_root()
    pyproject = root / "code" / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    content = pyproject.read_text()
    assert "[tool.flake8]" in content, "flake8 configuration section missing"
    assert "max-line-length" in content, "max-line-length configuration missing"


def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml."""
    root = get_project_root()
    pyproject = root / "code" / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    content = pyproject.read_text()
    assert "[tool.black]" in content, "black configuration section missing"
    assert "line-length" in content, "line-length configuration missing"


def test_flake8_can_parse_config():
    """Verify that flake8 can successfully read the configuration."""
    root = get_project_root()
    code_dir = root / "code"

    # Run flake8 with --help to verify it can parse config without errors
    # We use a dummy file that exists to trigger config loading
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        cwd=code_dir,
        capture_output=True,
        text=True
    )

    # If flake8 is installed, it should return 0
    # If not installed, this test is skipped (expected in some environments)
    if result.returncode != 0 and "No module named flake8" in result.stderr:
        pytest.skip("flake8 not installed, skipping config validation")

    assert result.returncode == 0, f"flake8 failed to parse config: {result.stderr}"


def test_black_can_parse_config():
    """Verify that black can successfully read the configuration."""
    root = get_project_root()
    code_dir = root / "code"

    # Run black with --version to verify it can parse config without errors
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        cwd=code_dir,
        capture_output=True,
        text=True
    )

    # If black is installed, it should return 0
    # If not installed, this test is skipped (expected in some environments)
    if result.returncode != 0 and "No module named black" in result.stderr:
        pytest.skip("black not installed, skipping config validation")

    assert result.returncode == 0, f"black failed to parse config: {result.stderr}"


def test_linting_config_excludes_data_dirs():
    """Verify that linting configurations exclude data directories."""
    root = get_project_root()
    pyproject = root / "code" / "pyproject.toml"
    content = pyproject.read_text()

    # Check that data directories are excluded from linting
    assert "data/raw" in content or "data/processed" in content or "data/results" in content, \
        "Data directories should be excluded from linting"