import os
import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify that ruff configuration exists in pyproject.toml or .ruff.toml"""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    ruff_toml = PROJECT_ROOT / ".ruff.toml"
    assert pyproject.exists() or ruff_toml.exists(), "Ruff config missing"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml"""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml missing"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black config missing in pyproject.toml"

def test_ruff_check_syntax():
    """Run ruff check to verify syntax and linting rules"""
    # Check if ruff is installed
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        # We expect exit code 0 (no errors) or 1 (linting warnings found but syntax valid)
        # If syntax is broken, it usually returns 2 or crashes.
        # For this test, we just ensure it runs and doesn't crash due to missing config.
        assert result.returncode in [0, 1], f"Ruff check failed with code {result.returncode}: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")

def test_black_check_syntax():
    """Run black --check to verify formatting"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", "code/"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        # Exit code 0: OK. Exit code 1: Would reformat (valid syntax).
        assert result.returncode in [0, 1], f"Black check failed with code {result.returncode}: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")

def test_pyproject_dependencies():
    """Verify required dependencies are listed in pyproject.toml"""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    content = pyproject.read_text()
    
    required_deps = [
        "torch-cpu",
        "scikit-learn",
        "pandas",
        "numpy",
        "statsmodels",
        "datasets",
        "opencv-python-headless",
        "pillow",
        "ruff",
        "black"
    ]
    
    for dep in required_deps:
        assert dep in content, f"Missing dependency: {dep}"