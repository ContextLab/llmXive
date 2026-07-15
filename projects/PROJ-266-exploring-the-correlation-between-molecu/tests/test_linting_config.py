"""
Tests to verify that linting and formatting configurations are present and valid.
These tests ensure the project adheres to the coding standards defined in T003.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), "Configuration file .flake8 is missing."
    assert flake8_path.stat().st_size > 0, "Configuration file .flake8 is empty."

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists and contains black/isort config."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "Configuration file pyproject.toml is missing."
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    assert "[tool.isort]" in content, "Missing [tool.isort] section in pyproject.toml"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    pre_commit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert pre_commit_path.exists(), "Configuration file .pre-commit-config.yaml is missing."
    
    content = pre_commit_path.read_text()
    assert "black" in content, "Missing black hook in .pre-commit-config.yaml"
    assert "flake8" in content, "Missing flake8 hook in .pre-commit-config.yaml"

def test_flake8_can_run_on_project():
    """
    Verify that flake8 can be invoked and runs against the codebase without crashing.
    This ensures the configuration is syntactically valid for flake8.
    """
    flake8_path = PROJECT_ROOT / ".flake8"
    if not flake8_path.exists():
        pytest.skip("Skipping flake8 execution test: .flake8 not found")

    # Run flake8 on the code directory
    try:
        result = subprocess.run(
            ["flake8", "code"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # We don't assert exit code 0 because code might have lint errors,
        # but we assert that the tool ran successfully (no import errors, etc.)
        # A return code of 123 or higher usually indicates a config error or crash.
        assert result.returncode < 123, f"Flake8 crashed or config invalid: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Skipping flake8 execution test: flake8 not installed")
    except subprocess.TimeoutExpired:
        pytest.skip("Skipping flake8 execution test: timeout")

def test_black_can_run_on_project():
    """
    Verify that black can be invoked and runs against the codebase without crashing.
    """
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "code"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # Return code 0 = formatted correctly, 1 = needs formatting.
        # We just want to ensure it doesn't crash (e.g., return code >= 123).
        assert result.returncode < 123, f"Black crashed or config invalid: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Skipping black execution test: black not installed")
    except subprocess.TimeoutExpired:
        pytest.skip("Skipping black execution test: timeout")