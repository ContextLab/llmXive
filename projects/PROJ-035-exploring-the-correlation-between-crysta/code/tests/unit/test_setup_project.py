import os
import tempfile
import pytest
from pathlib import Path
from setup_project import setup_project_structure

class TestSetupProject:
    """Unit tests for project structure creation."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            setup_project_structure(base_path)
            
            required_dirs = [
                "src",
                "tests",
                "data/raw",
                "data/cleaned",
                "data/results",
                "figures",
                "contracts"
            ]
            
            for dir_name in required_dirs:
                dir_path = base_path / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory"

    def test_nested_data_directories_created(self):
        """Verify that nested data directories (data/raw, etc.) are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            setup_project_structure(base_path)
            
            # Check specific nested paths
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "cleaned").exists()
            assert (base_path / "data" / "results").exists()

    def test_idempotent_operation(self):
        """Verify that running the function twice does not raise errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            # Run first time
            setup_project_structure(base_path)
            # Run second time
            setup_project_structure(base_path)
            
            # Verify structure still exists
            assert (base_path / "src").exists()
            assert (base_path / "contracts").exists()
            
    def test_existing_directory_not_overwritten(self):
        """Verify that existing directories are not modified unnecessarily."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            # Pre-create one directory
            (base_path / "src").mkdir()
            
            # Run setup
            setup_project_structure(base_path)
            
            # Verify it still exists and is a directory
            assert (base_path / "src").is_dir()
