"""
Unit tests for the project setup module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from project_setup import create_project_structure


class TestProjectSetup:
    """Tests for project directory creation."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_creates_code_directory(self):
        """Verify that the code/ directory is created."""
        create_project_structure()
        assert Path("code").is_dir()

    def test_creates_data_directories(self):
        """Verify that all required data subdirectories are created."""
        create_project_structure()
        assert Path("data/raw").is_dir()
        assert Path("data/processed").is_dir()
        assert Path("data/survey").is_dir()
        assert Path("data/synth").is_dir()

    def test_creates_test_directories(self):
        """Verify that test subdirectories are created."""
        create_project_structure()
        assert Path("tests/unit").is_dir()
        assert Path("tests/integration").is_dir()

    def test_creates_config_directory(self):
        """Verify that the config/ directory is created."""
        create_project_structure()
        assert Path("config").is_dir()

    def test_creates_docs_directory(self):
        """Verify that the docs/ directory is created."""
        create_project_structure()
        assert Path("docs").is_dir()

    def test_creates_figures_directory(self):
        """Verify that the figures/ directory is created."""
        create_project_structure()
        assert Path("figures").is_dir()

    def test_creates_gitkeep_files(self):
        """Verify that .gitkeep files are created in all directories."""
        create_project_structure()
        directories = [
            "code",
            "data/raw",
            "data/processed",
            "data/survey",
            "data/synth",
            "tests/unit",
            "tests/integration",
            "config",
            "docs",
            "figures",
        ]
        for dir_path in directories:
            gitkeep_path = Path(dir_path) / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep missing in {dir_path}"

    def test_idempotent_creation(self):
        """Verify that running the function twice doesn't cause errors."""
        create_project_structure()
        # Running again should not raise an exception
        create_project_structure()
        # Directories should still exist
        assert Path("code").is_dir()
        assert Path("data/raw").is_dir()
