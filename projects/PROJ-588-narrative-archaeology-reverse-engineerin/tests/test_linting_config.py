"""
Test suite to verify linting and formatting configuration.

These tests ensure that the project's linting rules (flake8, black, isort)
are correctly configured and that the codebase adheres to them.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent

@pytest.fixture
def project_root():
    return ROOT_DIR

def test_flake8_config_exists(project_root):
    """Verify .flake8 configuration file exists."""
    flake8_config = project_root / ".flake8"
    assert flake8_config.exists(), ".flake8 configuration file not found"
    
    content = flake8_config.read_text()
    assert "[flake8]" in content, ".flake8 missing [flake8] section"
    assert "max-line-length" in content, ".flake8 missing max-line-length setting"

def test_black_config_exists(project_root):
    """Verify black configuration in pyproject.toml."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length" in content, "pyproject.toml black config missing line-length"
    assert "88" in content, "black line-length should be 88"

def test_isort_config_exists(project_root):
    """Verify isort configuration in pyproject.toml."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    
    content = pyproject.read_text()
    assert "[tool.isort]" in content, "pyproject.toml missing [tool.isort] section"
    assert 'profile = "black"' in content, "isort should use black profile"

def test_pre_commit_config_exists(project_root):
    """Verify pre-commit configuration file exists."""
    pre_commit_config = project_root / ".pre-commit-config.yaml"
    assert pre_commit_config.exists(), ".pre-commit-config.yaml not found"
    
    content = pre_commit_config.read_text()
    assert "black" in content, "pre-commit config missing black hook"
    assert "flake8" in content, "pre-commit config missing flake8 hook"
    assert "isort" in content, "pre-commit config missing isort hook"

@pytest.mark.slow
def test_flake8_lints_cleanly(project_root):
    """Run flake8 on the codebase and verify no errors."""
    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        pytest.skip(".flake8 config not found, skipping lint check")
    
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--config=.flake8", "code/", "tests/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # flake8 returns 0 on success, 1 on lint errors
    if result.returncode != 0:
        pytest.fail(f"flake8 found lint errors:\n{result.stdout}\n{result.stderr}")

@pytest.mark.slow
def test_black_formatting_check(project_root):
    """Run black --check on the codebase and verify formatting."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "code/", "tests/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(f"black formatting check failed:\n{result.stdout}\n{result.stderr}")

@pytest.mark.slow
def test_isort_check(project_root):
    """Run isort --check on the codebase and verify import sorting."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check", "--diff", "code/", "tests/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(f"isort check failed:\n{result.stdout}\n{result.stderr}")
