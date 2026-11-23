import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from code.utils.setup_paths import ensure_project_dirs

class TestSetupPaths:
    """Unit tests for directory structure creation."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test_project"
            project_root.mkdir()
            
            # Run the function
            result_path = ensure_project_dirs(str(project_root))
            
            # Verify the root path is returned
            assert result_path == project_root
            
            # Define expected directories
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/reports",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "specs"
            ]
            
            # Assert each directory exists
            for dir_name in expected_dirs:
                dir_path = result_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_idempotent_creation(self):
        """Verify that running the function twice does not cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test_project"
            project_root.mkdir()
            
            # Run twice
            ensure_project_dirs(str(project_root))
            ensure_project_dirs(str(project_root))
            
            # Verify directories still exist
            expected_dirs = ["code", "data/raw", "data/processed", "data/reports", "tests/unit", "tests/integration", "tests/contract", "specs"]
            for dir_name in expected_dirs:
                assert (project_root / dir_name).exists()

    def test_creates_nested_directories(self):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test_project"
            project_root.mkdir()
            
            ensure_project_dirs(str(project_root))
            
            # Verify nested structure
            assert (project_root / "data").exists()
            assert (project_root / "data" / "raw").exists()
            assert (project_root / "data" / "processed").exists()
            assert (project_root / "data" / "reports").exists()
            assert (project_root / "tests").exists()
            assert (project_root / "tests" / "unit").exists()
            assert (project_root / "tests" / "integration").exists()
            assert (project_root / "tests" / "contract").exists()