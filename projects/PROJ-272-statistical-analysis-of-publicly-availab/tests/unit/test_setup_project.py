"""
Unit tests for the project setup utility (T001a).
Tests the directory creation functionality.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_project import create_directory

class TestSetupProject:
    """Test cases for directory creation."""

    def test_create_single_directory(self):
        """Test creating a single directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sub_dirs = ["data/raw"]
            result = create_directory(tmpdir, sub_dirs)
            
            assert result is True
            assert (Path(tmpdir) / "data/raw").exists()
            assert (Path(tmpdir) / "data/raw").is_dir()

    def test_create_nested_directories(self):
        """Test creating nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sub_dirs = [
                "data/raw",
                "data/interim",
                "data/results",
                "data/processed",
                "tests/unit",
                "tests/contract",
                "tests/integration",
                "specs/001-statistical-cognitive-decline/contracts"
            ]
            result = create_directory(tmpdir, sub_dirs)
            
            assert result is True
            for sub_dir in sub_dirs:
                full_path = Path(tmpdir) / sub_dir
                assert full_path.exists(), f"Directory {sub_dir} was not created"
                assert full_path.is_dir(), f"{sub_dir} is not a directory"

    def test_create_directories_when_base_exists(self):
        """Test that directories are created when base path exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create base structure first
            Path(tmpdir, "existing").mkdir()
            
            sub_dirs = ["new_dir"]
            result = create_directory(tmpdir, sub_dirs)
            
            assert result is True
            assert (Path(tmpdir) / "new_dir").exists()

    def test_create_directories_when_already_exists(self):
        """Test that existing directories don't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the directory first
            target_dir = Path(tmpdir) / "existing_dir"
            target_dir.mkdir()
            
            sub_dirs = ["existing_dir"]
            result = create_directory(tmpdir, sub_dirs)
            
            assert result is True
            assert target_dir.exists()

    def test_invalid_base_path(self):
        """Test behavior when base path doesn't exist."""
        sub_dirs = ["some_dir"]
        result = create_directory("/nonexistent/path/that/does/not/exist", sub_dirs)
        
        assert result is False

    def test_complex_nested_structure(self):
        """Test creating the full T001a structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Full structure from T001a
            sub_dirs = [
                "data/raw",
                "data/interim",
                "data/results",
                "data/processed",
                "code",
                "tests/unit",
                "tests/contract",
                "tests/integration",
                "specs/001-statistical-cognitive-decline/contracts"
            ]
            
            result = create_directory(tmpdir, sub_dirs)
            
            assert result is True
            
            # Verify each directory
            for sub_dir in sub_dirs:
                full_path = Path(tmpdir) / sub_dir
                assert full_path.exists(), f"Missing: {sub_dir}"
                assert full_path.is_dir(), f"Not a directory: {sub_dir}"

            # Verify the deepest nesting works
            deepest = Path(tmpdir) / "specs/001-statistical-cognitive-decline/contracts"
            assert deepest.exists()
            assert deepest.is_dir()
            # Verify parent directories also exist
            assert (Path(tmpdir) / "specs").exists()
            assert (Path(tmpdir) / "specs/001-statistical-cognitive-decline").exists()
