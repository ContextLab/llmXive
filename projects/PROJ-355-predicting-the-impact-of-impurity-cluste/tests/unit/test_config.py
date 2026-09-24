"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
from config import get_project_root, get_data_paths, get_config_summary

def test_get_project_root(project_root):
    """Test that get_project_root returns the correct path."""
    result = get_project_root()
    assert isinstance(result, Path)
    assert result.exists()

def test_get_data_paths(project_root):
    """Test that get_data_paths returns expected directories."""
    paths = get_data_paths()
    assert "raw" in paths
    assert "processed" in paths
    assert "results" in paths
    assert isinstance(paths["raw"], Path)

def test_get_config_summary(project_root):
    """Test that get_config_summary returns a dictionary."""
    summary = get_config_summary()
    assert isinstance(summary, dict)
    assert "project_root" in summary
    assert "random_seed" in summary
