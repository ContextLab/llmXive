"""
Unit tests for code/config.py configuration functions.
"""
import pytest
from pathlib import Path
import sys

# Ensure code is importable
project_root = Path(__file__).parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from config import get_project_root, get_data_paths, get_config_summary

def test_get_project_root():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_data_paths():
    """Test that get_data_paths returns expected directory structure."""
    paths = get_data_paths()
    assert isinstance(paths, dict)
    assert "raw" in paths
    assert "processed" in paths
    # Verify paths are Path objects
    for key, path in paths.items():
        assert isinstance(path, Path)

def test_get_config_summary():
    """Test that get_config_summary returns a dictionary with expected keys."""
    summary = get_config_summary()
    assert isinstance(summary, dict)
    # Check for essential keys
    assert "project_root" in summary
    assert "random_seed" in summary
