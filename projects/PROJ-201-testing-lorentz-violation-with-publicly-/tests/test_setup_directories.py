"""
Tests for T001: Directory structure creation.
"""
import os
import pytest
from pathlib import Path

from code.setup_directories import create_directories

def test_directories_exist_after_creation(tmp_path, monkeypatch):
    """Verify that create_directories creates the expected structure."""
    # Change to tmp_path to simulate project root
    monkeypatch.chdir(tmp_path)
    
    # Run the creation logic
    result = create_directories()
    
    assert result == 0, "Directory creation should return 0 on success"
    
    expected_dirs = [
        "code/data",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/results",
        "tests"
    ]
    
    for dir_name in expected_dirs:
        dir_path = tmp_path / dir_name
        assert dir_path.exists(), f"Directory {dir_name} should exist"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"
        
def test_idempotency(tmp_path, monkeypatch):
    """Verify that running the script twice doesn't fail."""
    monkeypatch.chdir(tmp_path)
    
    # Run twice
    result1 = create_directories()
    result2 = create_directories()
    
    assert result1 == 0
    assert result2 == 0
    
    # Check directories still exist
    expected_dirs = [
        "code/data",
        "data/raw",
        "tests"
    ]
    
    for dir_name in expected_dirs:
        assert (tmp_path / dir_name).exists()