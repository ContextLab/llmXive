"""
Tests to verify that the project's linting and formatting configuration is correct
and that the codebase complies with the configured standards.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def test_black_is_installed():
    """Test that black is installed and available."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Black not installed: {result.stderr}"
    assert "black" in result.stdout.lower()


def test_flake8_is_installed():
    """Test that flake8 is installed and available."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"flake8 not installed: {result.stderr}"


def test_isort_is_installed():
    """Test that isort is installed and available."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"isort not installed: {result.stderr}"


def test_gitignore_exists():
    """Test that .gitignore exists at project root."""
    project_root = get_project_root()
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore not found at project root"
    assert gitignore_path.is_file(), ".gitignore is not a file"


def test_setup_cfg_exists():
    """Test that .flake8 exists (using flake8 config file)."""
    project_root = get_project_root()
    flake8_path = project_root / ".flake8"
    assert flake8_path.exists(), ".flake8 not found at project root"
    assert flake8_path.is_file(), ".flake8 is not a file"


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists at project root."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found at project root"
    assert pyproject_path.is_file(), "pyproject.toml is not a file"


def test_requirements_txt_includes_dev_tools():
    """Test that requirements.txt includes dev tools (black, flake8, isort)."""
    project_root = get_project_root()
    requirements_path = project_root / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt not found"

    content = requirements_path.read_text()
    assert "black" in content.lower(), "black not in requirements.txt"
    assert "flake8" in content.lower(), "flake8 not in requirements.txt"
    assert "isort" in content.lower(), "isort not in requirements.txt"


@pytest.mark.skipif(
    not subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
    ).returncode
    == 0,
    reason="flake8 not installed",
)
def test_code_passes_flake8():
    """Test that the codebase passes flake8 checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "flake8", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"flake8 failed:\n{result.stdout}\n{result.stderr}"


@pytest.mark.skipif(
    not subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
    ).returncode
    == 0,
    reason="isort not installed",
)
def test_code_passes_isort():
    """Test that the codebase passes isort checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"isort failed:\n{result.stdout}\n{result.stderr}"


@pytest.mark.skipif(
    not subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
    ).returncode
    == 0,
    reason="black not installed",
)
def test_code_passes_black():
    """Test that the codebase passes black checks."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"black failed:\n{result.stdout}\n{result.stderr}"