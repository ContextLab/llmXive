"""
Tests for the data directory setup script.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_data_directories import create_directories, verify_structure, get_project_root

class TestDataDirectorySetup:
    @pytest.fixture(autouse=True)
    def setup_temp_environment(self, tmp_path):
        """
        Sets up a temporary directory structure for testing.
        """
        self.original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # Create a fake project structure
        project_root = tmp_path
        code_dir = project_root / "code"
        code_dir.mkdir()
        
        # Place the setup script in the code directory
        setup_script = code_dir / "setup_data_directories.py"
        shutil.copy(Path(__file__).parent.parent / "code" / "setup_data_directories.py", setup_script)
        
        yield tmp_path
        
        os.chdir(self.original_cwd)

    def test_create_directories_creates_raw(self, setup_temp_environment):
        """Test that create_directories creates the raw subdirectory."""
        result = create_directories()
        assert result is True
        data_dir = setup_temp_environment / "data"
        raw_dir = data_dir / "raw"
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_create_directories_creates_processed(self, setup_temp_environment):
        """Test that create_directories creates the processed subdirectory."""
        result = create_directories()
        assert result is True
        data_dir = setup_temp_environment / "data"
        processed_dir = data_dir / "processed"
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_create_directories_creates_results(self, setup_temp_environment):
        """Test that create_directories creates the results subdirectory."""
        result = create_directories()
        assert result is True
        data_dir = setup_temp_environment / "data"
        results_dir = data_dir / "results"
        assert results_dir.exists()
        assert results_dir.is_dir()

    def test_verify_structure_passes_after_creation(self, setup_temp_environment):
        """Test that verify_structure returns True after directories are created."""
        create_directories()
        result = verify_structure()
        assert result is True

    def test_verify_structure_fails_if_missing(self, setup_temp_environment):
        """Test that verify_structure returns False if a directory is missing."""
        # Create only the main data directory
        data_dir = setup_temp_environment / "data"
        data_dir.mkdir()
        # Do not create subdirectories
        
        result = verify_structure()
        assert result is False

    def test_get_project_root(self, setup_temp_environment):
        """Test that get_project_root returns the correct path."""
        project_root = get_project_root()
        assert project_root == setup_temp_environment