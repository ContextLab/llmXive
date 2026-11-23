import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# Assuming the test runs from the project root where 'code' is a sibling
# If running via pytest, ensure PYTHONPATH includes the project root
try:
    from setup_project_structure import create_structure
except ImportError:
    # Fallback for different import contexts if necessary
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from setup_project_structure import create_structure


class TestProjectStructure:
    """Tests for the project structure creation script."""

    def test_structure_creation(self, tmp_path):
        """Verify that the script creates the required directory hierarchy."""
        project_root = tmp_path / "PROJ-405"
        
        # Run the structure creation
        create_structure(str(project_root))
        
        # Verify root exists
        assert project_root.exists(), "Root project directory was not created"
        assert project_root.is_dir(), "Root path is not a directory"

        # Define expected directories relative to root
        expected_dirs = [
            "code",
            "data",
            "tests",
            "artifacts",
            "specs/001-predict-plant-disease-severity",
            "specs/001-predict-plant-disease-severity/contracts",
            "specs/001-predict-plant-disease-severity/data",
            "state",
            "figures",
            "data/raw",
            "data/processed",
            "data/interim",
        ]

        for subdir in expected_dirs:
            dir_path = project_root / subdir
            assert dir_path.exists(), f"Missing directory: {subdir}"
            assert dir_path.is_dir(), f"Path is not a directory: {subdir}"

    def test_gitkeep_files(self, tmp_path):
        """Verify that .gitkeep files are created in all directories."""
        project_root = tmp_path / "PROJ-405"
        create_structure(str(project_root))

        expected_dirs = [
            "code",
            "data",
            "tests",
            "artifacts",
            "specs/001-predict-plant-disease-severity",
            "specs/001-predict-plant-disease-severity/contracts",
            "specs/001-predict-plant-disease-severity/data",
            "state",
            "figures",
            "data/raw",
            "data/processed",
            "data/interim",
        ]

        for subdir in expected_dirs:
            dir_path = project_root / subdir
            gitkeep_path = dir_path / ".gitkeep"
            assert gitkeep_path.exists(), f"Missing .gitkeep in: {subdir}"
            assert gitkeep_path.is_file(), f".gitkeep is not a file in: {subdir}"

    def test_idempotency(self, tmp_path):
        """Verify that running the script twice does not cause errors."""
        project_root = tmp_path / "PROJ-405"
        
        # Run twice
        create_structure(str(project_root))
        create_structure(str(project_root))
        
        # Verify structure still exists and is valid
        assert (project_root / "code").exists()
        assert (project_root / "data").exists()
        assert (project_root / "tests").exists()