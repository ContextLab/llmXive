"""
Tests for linting and formatting configuration files.
Verifies that .ruff.toml and pyproject.toml exist and are non-empty.
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RUFF_CONFIG_PATH = PROJECT_ROOT / ".ruff.toml"
PYPROJECT_CONFIG_PATH = PROJECT_ROOT / "pyproject.toml"


def test_ruff_config_exists():
    """Verify that .ruff.toml exists and is non-empty."""
    assert RUFF_CONFIG_PATH.exists(), f".ruff.toml not found at {RUFF_CONFIG_PATH}"
    assert RUFF_CONFIG_PATH.stat().st_size > 0, ".ruff.toml is empty"
    
    # Verify content contains expected sections
    content = RUFF_CONFIG_PATH.read_text()
    assert "[lint]" in content, ".ruff.toml missing [lint] section"
    assert "select" in content, ".ruff.toml missing 'select' configuration"
    assert "[format]" in content, ".ruff.toml missing [format] section"
    assert "quote-style" in content, ".ruff.toml missing 'quote-style' configuration"


def test_black_config_exists():
    """Verify that pyproject.toml exists, is non-empty, and contains Black configuration."""
    assert PYPROJECT_CONFIG_PATH.exists(), f"pyproject.toml not found at {PYPROJECT_CONFIG_PATH}"
    assert PYPROJECT_CONFIG_PATH.stat().st_size > 0, "pyproject.toml is empty"
    
    # Verify content contains expected Black configuration
    content = PYPROJECT_CONFIG_PATH.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length" in content, "pyproject.toml missing 'line-length' configuration"
    assert "target-version" in content, "pyproject.toml missing 'target-version' configuration"
    assert "88" in content, "pyproject.toml line-length should be 88"
    assert "py311" in content, "pyproject.toml target-version should include py311"