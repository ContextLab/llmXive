"""
Tests for linting and formatting configuration.
Verifies that pyproject.toml exists and contains required sections for ruff and black.
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path to import config_linting
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config_linting import ensure_pyproject_toml

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def test_pyproject_toml_exists(project_root):
    """Test that pyproject.toml is created or exists."""
    pyproject_path = ensure_pyproject_toml()
    assert pyproject_path.exists(), "pyproject.toml should exist after running ensure_pyproject_toml"

def test_black_section_exists(project_root):
    """Test that pyproject.toml contains [tool.black] section."""
    ensure_pyproject_toml()
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "line-length" in content, "Black configuration must include line-length"

def test_ruff_section_exists(project_root):
    """Test that pyproject.toml contains [tool.ruff] section."""
    ensure_pyproject_toml()
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
    assert "line-length" in content, "Ruff configuration must include line-length"

def test_ruff_lint_section_exists(project_root):
    """Test that pyproject.toml contains [tool.ruff.lint] section."""
    ensure_pyproject_toml()
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "[tool.ruff.lint]" in content, "pyproject.toml must contain [tool.ruff.lint] section"

def test_ruff_format_section_exists(project_root):
    """Test that pyproject.toml contains [tool.ruff.format] section."""
    ensure_pyproject_toml()
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert "[tool.ruff.format]" in content, "pyproject.toml must contain [tool.ruff.format] section"