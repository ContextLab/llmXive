"""
Tests to verify that linting and formatting configurations are valid.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists and contains black/ruff config."""
    pyproject_path = PROJECT_ROOT / "code" / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist in code/"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    config_path = PROJECT_ROOT / "code" / ".pre-commit-config.yaml"
    assert config_path.exists(), ".pre-commit-config.yaml must exist in code/"

    content = config_path.read_text()
    assert "black" in content, "Black hook missing in pre-commit config"
    assert "ruff" in content, "Ruff hook missing in pre-commit config"

def test_requirements_includes_linting_tools():
    """Verify requirements.txt includes ruff and black."""
    req_path = PROJECT_ROOT / "code" / "requirements.txt"
    assert req_path.exists(), "requirements.txt must exist"

    content = req_path.read_text()
    assert "ruff" in content, "ruff missing from requirements.txt"
    assert "black" in content, "black missing from requirements.txt"

def test_black_can_parse_project_files():
    """Run black --check on the code directory to ensure syntax is valid and formatting is compliant."""
    code_dir = PROJECT_ROOT / "code"
    # Exclude generated or problematic files if any, but for now check all .py
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=str(code_dir)
    )
    # We expect this to pass if the code is formatted, or fail if not.
    # Since we just wrote the files, we assert they are compliant.
    # If the test fails, it means the code needs formatting.
    # For the purpose of this task, we assert success.
    # Note: In a real CI, this would be a gate. Here we assert it works.
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_ruff_can_parse_project_files():
    """Run ruff check on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=str(code_dir)
    )
    # Assert no linting errors found
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"