"""
Unit tests for the project structure setup script.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import create_structure

class TestProjectStructure:
    """Tests for the create_structure function."""

    def test_creates_required_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            
            base_path = Path(tmpdir)
            
            # Check main directories
            required_dirs = [
                "code/src/cli",
                "code/src/data",
                "code/src/models",
                "code/src/eval",
                "code/src/utils",
                "code/src/config",
                "code/tests/unit",
                "code/tests/integration",
                "code/tests/contract",
                "data/raw",
                "data/processed",
                "data/artifacts",
                "data/figures",
                "state",
                "docs",
                "logs",
            ]
            
            for dir_path in required_dirs:
                full_path = base_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_creates_init_files(self):
        """Test that __init__.py files are created for Python packages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            
            base_path = Path(tmpdir)
            
            init_files = [
                "code/src/__init__.py",
                "code/src/cli/__init__.py",
                "code/src/data/__init__.py",
                "code/src/models/__init__.py",
                "code/src/eval/__init__.py",
                "code/src/utils/__init__.py",
                "code/src/config/__init__.py",
                "code/tests/__init__.py",
                "code/tests/unit/__init__.py",
                "code/tests/integration/__init__.py",
                "code/tests/contract/__init__.py",
            ]
            
            for init_file in init_files:
                full_path = base_path / init_file
                assert full_path.exists(), f"Init file {init_file} was not created"
                assert full_path.is_file(), f"{init_file} exists but is not a file"

    def test_idempotent_creation(self):
        """Test that running create_structure twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First run
            create_structure(tmpdir)
            
            # Second run should not raise errors
            create_structure(tmpdir)
            
            # Verify directories still exist
            base_path = Path(tmpdir)
            assert (base_path / "state").exists()
            assert (base_path / "data/raw").exists()

    def test_nonexistent_base_directory(self):
        """Test that create_structure creates the base directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_base = Path(tmpdir) / "new_project_dir"
            create_structure(str(new_base))
            
            assert new_base.exists()
            assert (new_base / "state").exists()

    def test_existing_directory_structure(self):
        """Test that create_structure handles existing partial structures gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only one directory
            partial_dir = Path(tmpdir) / "code" / "src"
            partial_dir.mkdir(parents=True)
            
            # Running create_structure should not fail
            create_structure(tmpdir)
            
            # All directories should exist now
            assert (Path(tmpdir) / "state").exists()
            assert (Path(tmpdir) / "data/raw").exists()