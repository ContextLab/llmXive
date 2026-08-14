"""
Tests to verify linting and formatting configuration.
These tests ensure that the project adheres to the defined style guides.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def test_black_is_installed():
    """Verify black is available in the environment."""
    try:
        subprocess.run(
            ["black", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("black is not installed or not in PATH")


def test_flake8_is_installed():
    """Verify flake8 is available in the environment."""
    try:
        subprocess.run(
            ["flake8", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("flake8 is not installed or not in PATH")


def test_isort_is_installed():
    """Verify isort is available in the environment."""
    try:
        subprocess.run(
            ["isort", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("isort is not installed or not in PATH")


def test_gitignore_exists():
    """Verify .gitignore exists in the project root."""
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore not found in project root"


def test_setup_cfg_exists():
    """Verify setup.cfg exists for tool configuration."""
    project_root = get_project_root()
    setup_cfg_path = project_root / "setup.cfg"
    assert setup_cfg_path.exists(), "setup.cfg not found in project root"


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists for tool configuration."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found in project root"


def test_requirements_txt_includes_dev_tools():
    """Verify requirements.txt includes linting tools."""
    project_root = get_project_root()
    req_path = project_root / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"

    with open(req_path, "r") as f:
        content = f.read().lower()

    assert "black" in content, "black not in requirements.txt"
    assert "flake8" in content, "flake8 not in requirements.txt"
    assert "isort" in content, "isort not in requirements.txt"


@pytest.mark.lint
def test_code_passes_flake8():
    """Run flake8 on the codebase to check for style violations."""
    project_root = get_project_root()
    code_dir = project_root / "code"

    result = subprocess.run(
        [
            "flake8",
            "--config=setup.cfg",
            str(code_dir),
        ],
        capture_output=True,
        text=True,
    )

    # We expect flake8 to return non-zero if there are violations
    # In a real CI, this would fail the build. Here we assert it runs.
    # Note: If the codebase has violations, this test will fail.
    # For now, we assume the codebase is clean or we are just checking the tool runs.
    # If there are violations, the output will be in result.stdout
    if result.returncode != 0:
        pytest.fail(f"flake8 found violations:\n{result.stdout}")


@pytest.mark.lint
def test_code_passes_isort():
    """Run isort on the codebase to check for import order violations."""
    project_root = get_project_root()
    code_dir = project_root / "code"

    result = subprocess.run(
        [
            "isort",
            "--check-only",
            "--diff",
            str(code_dir),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"isort found violations:\n{result.stdout}")


@pytest.mark.lint
def test_code_passes_black():
    """Run black on the codebase to check for formatting violations."""
    project_root = get_project_root()
    code_dir = project_root / "code"

    result = subprocess.run(
        [
            "black",
            "--check",
            "--diff",
            str(code_dir),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"black found violations:\n{result.stdout}")