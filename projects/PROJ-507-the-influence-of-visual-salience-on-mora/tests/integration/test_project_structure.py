"""
Integration tests to verify the full project structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from project_setup import create_project_structure


class TestProjectStructureIntegration:
    """Integration tests for the complete project structure."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_complete_structure_exists(self):
        """Verify the entire required directory tree is present."""
        create_project_structure()

        required_paths = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/survey",
            "data/synth",
            "tests",
            "tests/unit",
            "tests/integration",
            "config",
            "docs",
            "figures",
        ]

        for path in required_paths:
            assert Path(path).exists(), f"Path {path} does not exist"
            assert Path(path).is_dir(), f"Path {path} is not a directory"

    def test_directory_hierarchy(self):
        """Verify that subdirectories are correctly nested under parents."""
        create_project_structure()

        # Check that data subdirectories are under data/
        assert (Path("data") / "raw").exists()
        assert (Path("data") / "processed").exists()
        assert (Path("data") / "survey").exists()
        assert (Path("data") / "synth").exists()

        # Check that test subdirectories are under tests/
        assert (Path("tests") / "unit").exists()
        assert (Path("tests") / "integration").exists()

    def test_structure_matches_spec(self):
        """
        Verify the structure matches the specification in tasks.md:
        - code/
        - data/raw/
        - data/processed/
        - data/survey/
        - tests/
        """
        create_project_structure()

        # Core requirements from T001
        assert Path("code").is_dir()
        assert Path("data/raw").is_dir()
        assert Path("data/processed").is_dir()
        assert Path("data/survey").is_dir()
        assert Path("tests").is_dir()

        # Ensure tests has subdirectories for organization
        assert Path("tests/unit").is_dir()
        assert Path("tests/integration").is_dir()