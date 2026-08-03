import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_ruff_config_exists():
    """Verify that .ruff.toml exists and is non-empty."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_path.exists(), ".ruff.toml not found in project root"
    assert ruff_path.stat().st_size > 0, ".ruff.toml is empty"
    
    content = ruff_path.read_text()
    assert "[lint]" in content, ".ruff.toml missing [lint] section"
    assert "[format]" in content, ".ruff.toml missing [format] section"
    assert 'select = ["E", "F", "W", "I"]' in content, ".ruff.toml missing correct select list"
    assert 'ignore = []' in content, ".ruff.toml missing empty ignore list"
    assert 'quote-style = "double"' in content, ".ruff.toml missing correct quote-style"

def test_black_config_exists():
    """Verify that pyproject.toml exists and contains correct Black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found in project root"
    assert pyproject_path.stat().st_size > 0, "pyproject.toml is empty"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length = 88" in content, "pyproject.toml missing correct line-length"
    assert "target-version = ['py311']" in content, "pyproject.toml missing correct target-version"