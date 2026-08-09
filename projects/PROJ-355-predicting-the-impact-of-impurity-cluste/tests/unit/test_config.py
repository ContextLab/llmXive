"""Unit tests for code/config.py."""
import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.config import get_project_root, get_data_paths, get_config_summary

def test_get_project_root():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_data_paths():
    """Test that get_data_paths returns expected directories."""
    paths = get_data_paths()
    assert 'raw' in paths
    assert 'processed' in paths
    assert isinstance(paths['raw'], Path)
    assert isinstance(paths['processed'], Path)

def test_get_config_summary():
    """Test that get_config_summary returns a dictionary."""
    summary = get_config_summary()
    assert isinstance(summary, dict)
    assert 'project_id' in summary or 'seed' in summary  # At least one config key
