import os
import pytest
from pathlib import Path
import shutil

class TestProjectStructure:
    """Tests for the project directory structure creation (T001a)."""
    
    BASE_DIR = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure clean state before and after tests."""
        # Clean up if exists
        if self.BASE_DIR.exists():
            shutil.rmtree(self.BASE_DIR)
        
        yield
        
        # Clean up after test
        if self.BASE_DIR.exists():
            shutil.rmtree(self.BASE_DIR)
    
    def test_create_structure_executes(self):
        """Verify that the create_structure function runs without error."""
        from create_project_structure import create_structure
        result = create_structure()
        assert result is True
    
    def test_base_directory_exists(self):
        """Verify the base project directory is created."""
        from create_project_structure import create_structure
        create_structure()
        assert self.BASE_DIR.exists(), "Base project directory should exist"
        assert self.BASE_DIR.is_dir(), "Base project directory should be a directory"
    
    def test_data_raw_exists(self):
        """Verify data/raw directory exists."""
        from create_project_structure import create_structure
        create_structure()
        data_raw = self.BASE_DIR / "data" / "raw"
        assert data_raw.exists(), "data/raw should exist"
        assert data_raw.is_dir(), "data/raw should be a directory"
    
    def test_data_processed_exists(self):
        """Verify data/processed directory exists."""
        from create_project_structure import create_structure
        create_structure()
        data_processed = self.BASE_DIR / "data" / "processed"
        assert data_processed.exists(), "data/processed should exist"
        assert data_processed.is_dir(), "data/processed should be a directory"
    
    def test_code_directory_exists(self):
        """Verify code directory exists."""
        from create_project_structure import create_structure
        create_structure()
        code_dir = self.BASE_DIR / "code"
        assert code_dir.exists(), "code directory should exist"
        assert code_dir.is_dir(), "code directory should be a directory"
    
    def test_tests_directory_exists(self):
        """Verify tests directory exists."""
        from create_project_structure import create_structure
        create_structure()
        tests_dir = self.BASE_DIR / "tests"
        assert tests_dir.exists(), "tests directory should exist"
        assert tests_dir.is_dir(), "tests directory should be a directory"
    
    def test_artifacts_checkpoints_exists(self):
        """Verify artifacts/checkpoints directory exists."""
        from create_project_structure import create_structure
        create_structure()
        checkpoints_dir = self.BASE_DIR / "artifacts" / "checkpoints"
        assert checkpoints_dir.exists(), "artifacts/checkpoints should exist"
        assert checkpoints_dir.is_dir(), "artifacts/checkpoints should be a directory"
    
    def test_artifacts_results_exists(self):
        """Verify artifacts/results directory exists."""
        from create_project_structure import create_structure
        create_structure()
        results_dir = self.BASE_DIR / "artifacts" / "results"
        assert results_dir.exists(), "artifacts/results should exist"
        assert results_dir.is_dir(), "artifacts/results should be a directory"
    
    def test_all_required_directories_created(self):
        """Verify all required directories from T001a are created."""
        from create_project_structure import create_structure
        create_structure()
        
        required_paths = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts/checkpoints",
            "artifacts/results"
        ]
        
        for rel_path in required_paths:
            full_path = self.BASE_DIR / rel_path
            assert full_path.exists(), f"Missing required directory: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"