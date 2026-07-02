"""
Unit tests to verify that linting and formatting configuration files exist
and contain expected settings.
"""
import os
from pathlib import Path

import pytest

# Path to the code directory relative to this test file
CODE_DIR = Path(__file__).parent.parent.parent / "code"

def test_ruff_config_exists():
    """Verify .ruff.toml exists."""
    ruff_config = CODE_DIR / ".ruff.toml"
    assert ruff_config.exists(), f"Ruff config not found at {ruff_config}"

def test_black_config_exists():
    """Verify .black.toml exists."""
    black_config = CODE_DIR / ".black.toml"
    assert black_config.exists(), f"Black config not found at {black_config}"

def test_requirements_dev_exists():
    """Verify requirements-dev.txt exists."""
    req_dev = CODE_DIR / "requirements-dev.txt"
    assert req_dev.exists(), f"Dev requirements not found at {req_dev}"

def test_ruff_config_contains_expected_settings():
    """Verify .ruff.toml contains key settings."""
    ruff_config = CODE_DIR / ".ruff.toml"
    content = ruff_config.read_text()
    
    assert "line-length" in content, "line-length setting missing in .ruff.toml"
    assert "target-version" in content, "target-version setting missing in .ruff.toml"
    assert "py311" in content, "Python 3.11 target version not specified"

def test_black_config_contains_expected_settings():
    """Verify .black.toml contains key settings."""
    black_config = CODE_DIR / ".black.toml"
    content = black_config.read_text()
    
    assert "line-length" in content, "line-length setting missing in .black.toml"
    assert "py311" in content, "Python 3.11 target version not specified"

def test_requirements_dev_contains_linting_tools():
    """Verify requirements-dev.txt includes ruff and black."""
    req_dev = CODE_DIR / "requirements-dev.txt"
    content = req_dev.read_text().lower()
    
    assert "ruff" in content, "ruff not found in requirements-dev.txt"
    assert "black" in content, "black not found in requirements-dev.txt"