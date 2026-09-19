"""
Tests for the project structure setup module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_structure import create_project_structure


class TestCreateProjectStructure:
    """Tests for create_project_structure function."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "test_project"
            
            create_project_structure(str(base_path))
            
            # Check root exists
            assert base_path.exists()
            assert base_path.is_dir()
            
            # Check all required subdirectories
            required_dirs = [
                "data/raw",
                "data/processed",
                "results",
                "code",
                "tests"
            ]
            
            for dir_name in required_dirs:
                dir_path = base_path / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_creates_init_files(self):
        """Verify that __init__.py files are created in code and tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "test_project"
            
            create_project_structure(str(base_path))
            
            code_init = base_path / "code" / "__init__.py"
            tests_init = base_path / "tests" / "__init__.py"
            
            assert code_init.exists(), "code/__init__.py was not created"
            assert tests_init.exists(), "tests/__init__.py was not created"

    def test_idempotent_execution(self):
        """Verify that running the function twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "test_project"
            
            # Run twice
            create_project_structure(str(base_path))
            create_project_structure(str(base_path))
            
            # Verify structure is intact
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "processed").exists()
            assert (base_path / "results").exists()
            assert (base_path / "code").exists()
            assert (base_path / "tests").exists()

    def test_creates_nested_directories(self):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "test_project"
            
            create_project_structure(str(base_path))
            
            # Verify nested structure
            assert (base_path / "data").exists()
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "processed").exists()
            
            # Verify they are distinct directories
            assert (base_path / "data" / "raw") != (base_path / "data" / "processed")