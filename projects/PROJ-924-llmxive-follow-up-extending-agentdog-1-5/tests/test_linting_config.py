"""
Tests for T010: Verify linting and formatting configuration files exist and are non-empty.
"""
import os
import pytest
from pathlib import Path

# Project root relative to test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUFF_CONFIG_PATH = PROJECT_ROOT / ".ruff.toml"
BLACK_CONFIG_PATH = PROJECT_ROOT / "pyproject.toml"

def test_ruff_config_exists():
    """Verify .ruff.toml exists and is non-empty."""
    assert RUFF_CONFIG_PATH.exists(), f".ruff.toml not found at {RUFF_CONFIG_PATH}"
    assert RUFF_CONFIG_PATH.stat().st_size > 0, ".ruff.toml is empty"

    content = RUFF_CONFIG_PATH.read_text()
    assert "[lint]" in content, ".ruff.toml missing [lint] section"
    assert 'select = ["E", "F", "W", "I"]' in content, ".ruff.toml missing correct select list"
    assert "[format]" in content, ".ruff.toml missing [format] section"
    assert 'quote-style = "double"' in content, ".ruff.toml missing quote-style setting"

def test_black_config_exists():
    """Verify pyproject.toml exists, is non-empty, and contains Black settings."""
    assert BLACK_CONFIG_PATH.exists(), f"pyproject.toml not found at {BLACK_CONFIG_PATH}"
    assert BLACK_CONFIG_PATH.stat().st_size > 0, "pyproject.toml is empty"

    content = BLACK_CONFIG_PATH.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"
    assert "line-length = 88" in content, "pyproject.toml missing line-length setting"
    assert "target-version = ['py311']" in content, "pyproject.toml missing target-version setting"