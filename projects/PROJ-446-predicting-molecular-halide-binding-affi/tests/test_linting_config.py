"""
Tests for linting and formatting configuration.
Verifies that configuration files exist and are valid.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

CONFIG_FILES = [".ruff.toml", ".black.toml", ".flake8"]

def test_config_files_exist():
    """Ensure all required linting/formatting config files exist."""
    for filename in CONFIG_FILES:
        filepath = CODE_DIR / filename
        assert filepath.exists(), f"Configuration file {filename} is missing"
        assert filepath.stat().st_size > 0, f"Configuration file {filename} is empty"

def test_ruff_config_syntax():
    """Verify ruff config is valid TOML."""
    try:
        import tomli
    except ImportError:
        pytest.skip("tomli not installed")

    filepath = CODE_DIR / ".ruff.toml"
    with open(filepath, "rb") as f:
        try:
            tomli.load(f)
        except Exception as e:
            pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

def test_black_config_syntax():
    """Verify black config is valid TOML."""
    try:
        import tomli
    except ImportError:
        pytest.skip("tomli not installed")

    filepath = CODE_DIR / ".black.toml"
    with open(filepath, "rb") as f:
        try:
            tomli.load(f)
        except Exception as e:
            pytest.fail(f"Invalid TOML in .black.toml: {e}")

def test_flake8_config_syntax():
    """Verify flake8 config is valid INI."""
    import configparser

    filepath = CODE_DIR / ".flake8"
    config = configparser.ConfigParser()
    try:
        config.read(filepath)
        assert "flake8" in config, ".flake8 must have a [flake8] section"
    except Exception as e:
        pytest.fail(f"Invalid INI in .flake8: {e}")

def test_requirements_includes_linting_tools():
    """Verify requirements.txt includes ruff, black, and flake8."""
    filepath = CODE_DIR / "requirements.txt"
    content = filepath.read_text().lower()
    
    assert "ruff" in content, "ruff must be in requirements.txt"
    assert "black" in content, "black must be in requirements.txt"
    assert "flake8" in content, "flake8 must be in requirements.txt"