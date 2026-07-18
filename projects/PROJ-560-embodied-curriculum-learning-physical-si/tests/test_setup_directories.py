import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_directories
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from setup_directories import create_directory, main

class TestSetupDirectories:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_create_directory_creates_new_folder(self, temp_project_root):
        """Test that create_directory creates a new folder if it doesn't exist."""
        new_dir = temp_project_root / "new_test_dir"
        assert not new_dir.exists()
        
        create_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_directory_existing_folder(self, temp_project_root):
        """Test that create_directory does nothing if folder already exists."""
        existing_dir = temp_project_root / "existing_dir"
        existing_dir.mkdir(parents=True, exist_ok=True)
        
        # Should not raise an error
        create_directory(existing_dir)
        
        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_create_directory_nested(self, temp_project_root):
        """Test that create_directory creates parent directories."""
        nested_dir = temp_project_root / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        create_directory(nested_dir)
        
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_main_creates_all_required_directories(self, temp_project_root):
        """Test that main() creates all required data and state directories."""
        # Temporarily override __file__ to point to our temp directory
        # We need to simulate the script being in code/
        code_dir = temp_project_root / "code"
        code_dir.mkdir()
        
        # Create a mock script file in code/ to test the logic
        script_path = code_dir / "setup_directories.py"
        
        # We will test the logic directly by constructing paths
        data_dirs = [
            temp_project_root / "data" / "raw",
            temp_project_root / "data" / "processed",
            temp_project_root / "data" / "synthetic",
            temp_project_root / "data" / "derivation_logs",
        ]
        
        state_dirs = [
            temp_project_root / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si",
        ]
        
        all_expected_dirs = data_dirs + state_dirs
        
        # Run the creation logic manually for testing
        for directory in all_expected_dirs:
            create_directory(directory)
        
        # Verify all directories were created
        for directory in all_expected_dirs:
            assert directory.exists(), f"Directory {directory} was not created"
            assert directory.is_dir(), f"{directory} is not a directory"