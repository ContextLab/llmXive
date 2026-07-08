"""
Tests for the config package initialization and path resolution.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import CONFIG_ROOT, STRUCTURAL_ALERTS_FILE, get_config_path

def test_config_root_exists():
    """Verify the config root directory exists."""
    assert CONFIG_ROOT.exists(), "Config root directory must exist"
    assert CONFIG_ROOT.is_dir(), "Config root must be a directory"

def test_config_root_is_parent():
    """Verify config root is the parent of this file's module."""
    # CONFIG_ROOT should be the directory containing __init__.py
    init_file = CONFIG_ROOT / "__init__.py"
    assert init_file.exists(), "__init__.py must exist in config root"

def test_structural_alerts_file_defined():
    """Verify the structural alerts file path is defined."""
    assert STRUCTURAL_ALERTS_FILE is not None
    assert isinstance(STRUCTURAL_ALERTS_FILE, Path)

def test_get_config_path_returns_absolute():
    """Verify get_config_path returns an absolute path."""
    result = get_config_path("test.json")
    assert result.is_absolute(), "get_config_path must return absolute path"

def test_get_config_path_resolves_correctly():
    """Verify get_config_path resolves relative to CONFIG_ROOT."""
    result = get_config_path("alerts.json")
    expected = CONFIG_ROOT / "alerts.json"
    assert result == expected, f"Expected {expected}, got {result}"