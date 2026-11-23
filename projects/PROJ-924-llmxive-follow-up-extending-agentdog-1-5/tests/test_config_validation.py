"""
Tests for T010: Verify linting and formatting configuration files exist and are non-empty.
"""
import os
import pytest
from pathlib import Path

# Project root relative to test file location (assuming tests/ is at project root)
PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify .ruff.toml exists and is non-empty."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_path.exists(), f"File not found: {ruff_path}"
    assert ruff_path.stat().st_size > 0, f"File is empty: {ruff_path}"
    
    content = ruff_path.read_text()
    assert "[lint]" in content, ".ruff.toml missing [lint] section"
    assert "[format]" in content, ".ruff.toml missing [format] section"

def test_black_config_exists():
    """Verify pyproject.toml exists, is non-empty, and contains Black config."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"File not found: {pyproject_path}"
    assert pyproject_path.stat().st_size > 0, f"File is empty: {pyproject_path}"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length" in content, "pyproject.toml missing line-length setting"
    assert "target-version" in content, "pyproject.toml missing target-version setting"