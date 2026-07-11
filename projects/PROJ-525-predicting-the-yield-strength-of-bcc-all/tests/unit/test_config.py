"""
Unit tests for configuration management in code/config.py.
"""
import pytest
import os
from pathlib import Path
from config import ensure_dirs

class TestConfig:
    """Test suite for configuration functions."""

    def test_ensure_dirs_creates_directories(self, tmp_path):
        """Test that ensure_dirs creates the specified directories."""
        # Create a temporary directory structure to test
        test_root = tmp_path / "test_project"
        dirs_to_create = [
            test_root / "data" / "raw",
            test_root / "data" / "processed",
            test_root / "code" / "utils",
            test_root / "tests" / "unit"
        ]
        
        # Ensure the function works with Path objects
        ensure_dirs(test_root, dirs_to_create)
        
        for dir_path in dirs_to_create:
            assert dir_path.exists(), f"Directory {dir_path} should exist"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"

    def test_ensure_dirs_handles_existing(self, tmp_path):
        """Test that ensure_dirs doesn't fail if directories already exist."""
        test_root = tmp_path / "existing_project"
        existing_dir = test_root / "data" / "raw"
        existing_dir.mkdir(parents=True)
        
        # Should not raise an exception
        ensure_dirs(test_root, [existing_dir])
        assert existing_dir.exists()
