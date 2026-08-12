import os
import pytest
from pathlib import Path
import shutil

# Import the function to test
import sys
sys.path.insert(0, 'code')
from create_project_structure import create_structure

class TestProjectStructure:
    """Tests for the project directory structure creation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        self.base_path = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
        
        # Cleanup before test if exists
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        
        yield
        
        # Cleanup after test
        if self.base_path.exists():
            shutil.rmtree(self.base_path)

    def test_create_structure_executes(self):
        """Test that the create_structure function runs without error."""
        result = create_structure()
        assert result is True

    def test_base_directory_exists(self):
        """Test that the base project directory is created."""
        create_structure()
        assert self.base_path.exists()
        assert self.base_path.is_dir()

    def test_data_raw_directory_exists(self):
        """Test that data/raw directory is created."""
        create_structure()
        raw_dir = self.base_path / "data" / "raw"
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_data_processed_directory_exists(self):
        """Test that data/processed directory is created."""
        create_structure()
        processed_dir = self.base_path / "data" / "processed"
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_code_directory_exists(self):
        """Test that code directory is created."""
        create_structure()
        code_dir = self.base_path / "code"
        assert code_dir.exists()
        assert code_dir.is_dir()

    def test_tests_directory_exists(self):
        """Test that tests directory is created."""
        create_structure()
        tests_dir = self.base_path / "tests"
        assert tests_dir.exists()
        assert tests_dir.is_dir()

    def test_artifacts_checkpoints_directory_exists(self):
        """Test that artifacts/checkpoints directory is created."""
        create_structure()
        checkpoints_dir = self.base_path / "artifacts" / "checkpoints"
        assert checkpoints_dir.exists()
        assert checkpoints_dir.is_dir()

    def test_artifacts_results_directory_exists(self):
        """Test that artifacts/results directory is created."""
        create_structure()
        results_dir = self.base_path / "artifacts" / "results"
        assert results_dir.exists()
        assert results_dir.is_dir()

    def test_artifacts_figures_directory_exists(self):
        """Test that artifacts/figures directory is created."""
        create_structure()
        figures_dir = self.base_path / "artifacts" / "figures"
        assert figures_dir.exists()
        assert figures_dir.is_dir()

    def test_full_hierarchy_exists(self):
        """Test that the entire required hierarchy exists."""
        create_structure()
        
        required_paths = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts/checkpoints",
            "artifacts/results",
            "artifacts/figures"
        ]
        
        for path_str in required_paths:
            full_path = self.base_path / path_str
            assert full_path.exists(), f"Missing directory: {full_path}"
            assert full_path.is_dir(), f"Not a directory: {full_path}"
