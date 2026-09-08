import os
import shutil
import tempfile
import pytest
from pathlib import Path
from code.create_project_structure import create_structure

class TestCreateProjectStructure:
    """Tests for the project structure creation logic."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_all_directories(self):
        """Verify that all required directories are created."""
        create_structure(self.temp_dir)
        
        project_name = "PROJ-558-consciousness-bootstrapping-self-aware-a"
        base_path = Path(self.temp_dir) / "projects" / project_name
        
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts/checkpoints",
            "artifacts/reports"
        ]
        
        for subdir in expected_dirs:
            full_path = base_path / subdir
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_creates_parent_directories(self):
        """Verify that parent directories (projects/) are created automatically."""
        create_structure(self.temp_dir)
        
        projects_dir = Path(self.temp_dir) / "projects"
        assert projects_dir.exists(), "Parent 'projects' directory was not created"
        assert projects_dir.is_dir(), "'projects' is not a directory"
