"""
Unit tests for the directory setup functionality (Task T001).
"""
import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the functions to test
from setup_directories import ensure_directories, validate_paths

def test_ensure_directories_creates_all_folders():
    """Test that ensure_directories creates all required folders."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        result = ensure_directories(base_path)
        
        assert result is True
        
        required_dirs = [
            "data/raw",
            "data/processed",
            "artifacts",
            "state",
            "code",
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            assert dir_path.is_dir(), f"Directory {dir_path} was not created."

def test_validate_paths_returns_true_when_all_exist():
    """Test that validate_paths returns True when all directories exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Create directories first
        ensure_directories(base_path)
        
        result = validate_paths(base_path)
        
        assert result is True

def test_validate_paths_returns_false_when_missing():
    """Test that validate_paths returns False when a directory is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Only create a subset
        (base_path / "data").mkdir()
        (base_path / "data" / "raw").mkdir()
        
        # Missing others
        result = validate_paths(base_path)
        
        assert result is False

def test_ensure_directories_idempotent():
    """Test that running ensure_directories twice does not cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Run twice
        result1 = ensure_directories(base_path)
        result2 = ensure_directories(base_path)
        
        assert result1 is True
        assert result2 is True
        
        # Verify structure still correct
        assert validate_paths(base_path) is True