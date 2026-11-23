"""
Tests for directory creation functionality.
Verifies that all required project directories are created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from create_directories import ensure_directories, REQUIRED_DIRS

class TestEnsureDirectories:
    """Test suite for ensure_directories function."""

    def test_creates_all_required_directories(self):
        """Verify all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            created = ensure_directories(base_path)
            
            # Check count
            assert len(created) == len(REQUIRED_DIRS), \
                f"Expected {len(REQUIRED_DIRS)} directories, got {len(created)}"
            
            # Check each directory exists
            for dir_path in REQUIRED_DIRS:
                full_path = base_path / dir_path
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_handles_existing_directories(self):
        """Verify function doesn't fail if directories already exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create directories once
            first_run = ensure_directories(base_path)
            assert len(first_run) == len(REQUIRED_DIRS)
            
            # Run again - should succeed without error
            second_run = ensure_directories(base_path)
            assert len(second_run) == len(REQUIRED_DIRS)

    def test_creates_nested_directories(self):
        """Verify nested directories (e.g., data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            ensure_directories(base_path)
            
            # Check nested directories
            nested_dirs = ["data/raw", "data/processed", "data/test", "specs/001-llmxive-drift-detection"]
            for dir_path in nested_dirs:
                full_path = base_path / dir_path
                assert full_path.exists(), f"Nested directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_returns_absolute_paths(self):
        """Verify returned paths are absolute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            created = ensure_directories(base_path)
            
            for path_str in created:
                path_obj = Path(path_str)
                assert path_obj.is_absolute(), f"Path {path_str} is not absolute"

    def test_required_dirs_list_complete(self):
        """Verify REQUIRED_DIRS includes all task requirements."""
        expected_dirs = {
            "code", "tests", "data/raw", "data/processed", 
            "data/test", "specs", "docs", "specs/001-llmxive-drift-detection"
        }
        actual_dirs = set(REQUIRED_DIRS)
        
        assert expected_dirs == actual_dirs, \
            f"REQUIRED_DIRS mismatch. Missing: {expected_dirs - actual_dirs}, Extra: {actual_dirs - expected_dirs}"
