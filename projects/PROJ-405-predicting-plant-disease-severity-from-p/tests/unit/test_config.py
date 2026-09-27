"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
import sys

# Ensure imports work
from config import get_path, ensure_dirs

def test_get_path_relative():
    """Test that get_path returns the correct absolute path for a relative input."""
    p = get_path("data/processed/test.csv")
    assert isinstance(p, Path)
    assert p.name == "test.csv"
    assert "data" in str(p)

def test_ensure_dirs_creates_directory(tmp_path, monkeypatch):
    """Test that ensure_dirs creates the directory if it doesn't exist."""
    # Monkeypatch the base path to tmp_path for isolation
    monkeypatch.setattr("config.BASE_DIR", tmp_path)
    
    target_dir = tmp_path / "new_dir" / "nested"
    assert not target_dir.exists()
    
    ensure_dirs([str(target_dir)])
    
    assert target_dir.exists()
    assert target_dir.is_dir()
