import os
import subprocess
import sys
import pytest
from pathlib import Path

# Determine project root (assuming tests are in code/tests/unit)
# This path calculation assumes the repo root is two levels up from this file
# if the structure is code/tests/unit/test_linting_config.py
# However, based on the API surface, tests are at code/tests/
# So project root is likely code/ relative to the repo root if code/ is the root.
# Let's assume the repo root is where pyproject.toml lives.
# If running from code/tests/unit, we go up to code/ then look for pyproject.toml.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists at the project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_ruff_config_present():
    """Verify that Ruff configuration is present (either in pyproject.toml or .ruff.toml)."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    ruff_toml_path = PROJECT_ROOT / ".ruff.toml"
    
    has_config = False
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.ruff]" in content:
            has_config = True
    
    if not has_config and ruff_toml_path.exists():
        has_config = True
    
    assert has_config, "Ruff configuration not found in pyproject.toml or .ruff.toml"

def test_black_config_present():
    """Verify that Black configuration is present (either in pyproject.toml or .black.toml)."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    black_toml_path = PROJECT_ROOT / ".black.toml"
    
    has_config = False
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            has_config = True
    
    if not has_config and black_toml_path.exists():
        has_config = True
    
    assert has_config, "Black configuration not found in pyproject.toml or .black.toml"

def test_ruff_check_executable():
    """Verify that ruff is installed and can run a check (dry-run)."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Ruff not installed or failed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("Ruff is not installed in the environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")

def test_black_check_executable():
    """Verify that black is installed and can run a check (dry-run)."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Black not installed or failed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("Black is not installed in the environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")