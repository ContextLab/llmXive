import os
import pytest
from pathlib import Path

# Determine project root relative to this test file
# The test file is at tests/test_config_files.py
# Project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_ruff_config_exists():
    """Verify .ruff.toml exists and is non-empty."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_path.exists(), f"File not found: {ruff_path}"
    assert ruff_path.stat().st_size > 0, f"File is empty: {ruff_path}"

def test_black_config_exists():
    """Verify pyproject.toml exists, is non-empty, and contains Black config."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"File not found: {pyproject_path}"
    assert pyproject_path.stat().st_size > 0, f"File is empty: {pyproject_path}"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"