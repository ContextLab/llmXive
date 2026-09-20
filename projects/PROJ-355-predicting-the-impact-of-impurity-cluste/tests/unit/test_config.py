"""Unit tests for code/config.py."""
import pytest
from pathlib import Path
import sys

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_project_root, get_data_paths, get_config_summary

def test_get_project_root():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_data_paths():
    """Test that get_data_paths returns a dictionary with expected keys."""
    paths = get_data_paths()
    assert isinstance(paths, dict)
    assert "raw" in paths
    assert "processed" in paths
    # Check that paths are Path objects
    for key, path in paths.items():
        assert isinstance(path, Path)

def test_get_config_summary():
    """Test that get_config_summary returns a dictionary."""
    summary = get_config_summary()
    assert isinstance(summary, dict)
    # Basic check for expected keys
    assert "project_name" in summary or "seed" in summary or "paths" in summary
