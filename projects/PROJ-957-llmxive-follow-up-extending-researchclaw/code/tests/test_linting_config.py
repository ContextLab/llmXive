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
    
    assert (pyproject.exists() or ruff_toml.exists()), \
        "Ruff configuration file (pyproject.toml or .ruff.toml) not found"
    
    if pyproject.exists():
        content = pyproject.read_text()
        assert "[tool.ruff]" in content, \
            "Ruff configuration section missing from pyproject.toml"

def test_black_config_exists():
    """Verify that Black configuration exists in pyproject.toml"""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml not found"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, \
        "Black configuration section missing from pyproject.toml"
    assert "line-length" in content, \
        "Black line-length configuration missing"

def test_pyproject_dev_dependencies():
    """Verify that dev dependencies (ruff, black) are listed in pyproject.toml"""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml not found"
    
    content = pyproject.read_text()
    assert "ruff" in content, "ruff not found in dependencies"
    assert "black" in content, "black not found in dependencies"

def test_ruff_check_syntax():
    """Run ruff check to verify syntax and linting rules are valid"""
    ruff_path = PROJECT_ROOT / "pyproject.toml"
    
    # Check if ruff is installed
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("ruff is not installed")
    
    # Run ruff check on the code directory
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        pytest.skip("code directory not found")
    
    result = subprocess.run(
        ["ruff", "check", str(code_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # We expect ruff to run successfully (exit code 0 or 1 for found issues)
    # Exit code 2 indicates a configuration error
    assert result.returncode != 2, \
        f"Ruff configuration error: {result.stderr}"

def test_black_check_syntax():
    """Run black --check to verify formatting rules are valid"""
    # Check if black is installed
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("black is not installed")
    
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        pytest.skip("code directory not found")
    
    result = subprocess.run(
        ["black", "--check", "--diff", str(code_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # Exit code 0: all files are formatted correctly
    # Exit code 1: some files need reformatting (this is okay for the test itself)
    # Exit code >= 2: configuration or runtime error
    assert result.returncode < 2, \
        f"Black configuration error: {result.stderr}"