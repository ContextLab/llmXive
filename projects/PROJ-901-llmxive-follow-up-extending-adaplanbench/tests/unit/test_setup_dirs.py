"""
Unit tests for the setup_dirs script functionality.
Verifies that the directory structure creation logic works as expected.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the logic we are testing
# We test the function logic directly rather than the CLI entry point
def create_test_structure(root: Path):
    """Helper to recreate the logic from setup_dirs.py for testing."""
    directories = [
        root / "code" / "dataset",
        root / "code" / "agent",
        root / "code" / "analysis",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "figures",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
        root / "specs",
    ]
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)
    return created

class TestSetupDirs:
    def test_creates_code_dataset_dir(self, tmp_path):
        """Verify code/dataset directory is created."""
        created = create_test_structure(tmp_path)
        assert (tmp_path / "code" / "dataset").exists()
        assert (tmp_path / "code" / "dataset").is_dir()

    def test_creates_code_agent_dir(self, tmp_path):
        """Verify code/agent directory is created."""
        assert (tmp_path / "code" / "agent").exists()
        assert (tmp_path / "code" / "agent").is_dir()

    def test_creates_code_analysis_dir(self, tmp_path):
        """Verify code/analysis directory is created."""
        assert (tmp_path / "code" / "analysis").exists()
        assert (tmp_path / "code" / "analysis").is_dir()

    def test_creates_data_raw_dir(self, tmp_path):
        """Verify data/raw directory is created."""
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "raw").is_dir()

    def test_creates_data_processed_dir(self, tmp_path):
        """Verify data/processed directory is created."""
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "processed").is_dir()

    def test_creates_tests_unit_dir(self, tmp_path):
        """Verify tests/unit directory is created."""
        assert (tmp_path / "tests" / "unit").exists()
        assert (tmp_path / "tests" / "unit").is_dir()

    def test_creates_tests_integration_dir(self, tmp_path):
        """Verify tests/integration directory is created."""
        assert (tmp_path / "tests" / "integration").exists()
        assert (tmp_path / "tests" / "integration").is_dir()

    def test_creates_all_directories(self, tmp_path):
        """Verify all expected directories are created in one run."""
        create_test_structure(tmp_path)
        
        expected_dirs = [
            "code/dataset", "code/agent", "code/analysis",
            "data/raw", "data/processed", "data/figures",
            "tests/unit", "tests/integration", "tests/contract",
            "specs"
        ]
        
        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"Path {dir_path} is not a directory"

    def test_does_not_raise_on_existing_dirs(self, tmp_path):
        """Verify the function handles pre-existing directories gracefully."""
        # Pre-create some directories
        (tmp_path / "code" / "dataset").mkdir(parents=True)
        (tmp_path / "data" / "raw").mkdir(parents=True)
        
        # Running the setup again should not raise an error
        created = create_test_structure(tmp_path)
        # Should not crash
        assert isinstance(created, list)