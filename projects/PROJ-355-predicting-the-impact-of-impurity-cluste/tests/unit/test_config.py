"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
from config import get_project_root, get_data_paths, get_config_summary

def test_get_project_root():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_data_paths():
    """Test that get_data_paths returns the expected directory structure."""
    paths = get_data_paths()
    
    assert "raw" in paths
    assert "processed" in paths
    assert "results" in paths
    
    # Check that paths are Path objects
    for key, path in paths.items():
        assert isinstance(path, Path)

def test_get_config_summary():
    """Test that get_config_summary returns a dictionary with expected keys."""
    summary = get_config_summary()
    
    assert isinstance(summary, dict)
    # At minimum, it should contain basic configuration info
    assert "project_root" in summary or "random_seed" in summary or "data_paths" in summary
