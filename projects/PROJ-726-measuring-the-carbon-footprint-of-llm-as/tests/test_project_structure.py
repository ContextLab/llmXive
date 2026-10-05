import os
import pytest
from pathlib import Path
import shutil
import tempfile

from code.setup_project_structure import create_directory_structure

class TestProjectStructure:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup after test
        shutil.rmtree(temp_dir)

    def test_creates_all_required_directories(self, temp_project_root):
        """Test that create_directory_structure creates all required folders."""
        create_directory_structure(temp_project_root)
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/outputs",
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = temp_project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_nested_directories_created(self, temp_project_root):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        create_directory_structure(temp_project_root)
        
        nested_dirs = [
            "data/raw",
            "data/processed",
            "data/outputs"
        ]
        
        for dir_name in nested_dirs:
            dir_path = temp_project_root / dir_name
            assert dir_path.exists(), f"Nested directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_idempotent_creation(self, temp_project_root):
        """Test that running the function twice doesn't cause errors."""
        # First run
        create_directory_structure(temp_project_root)
        
        # Second run
        create_directory_structure(temp_project_root)
        
        # Verify still exists
        assert (temp_project_root / "code").exists()
        assert (temp_project_root / "data/raw").exists()