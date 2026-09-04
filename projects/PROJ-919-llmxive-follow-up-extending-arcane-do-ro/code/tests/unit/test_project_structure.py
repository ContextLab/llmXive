import os
import tempfile
import pytest
from pathlib import Path
import sys

# Import the setup logic
# Note: The import path assumes this test file is run from the project root or
# the code directory is in sys.path. The setup_project_structure.py is in code/.
# We need to adjust sys.path to import from code/setup_project_structure
import setup_project_structure

class TestProjectStructure:
    """Tests to verify that the project directory structure is created correctly."""

    def test_setup_directories_creates_structure(self, tmp_path):
        """Verify that setup_directories creates all required directories."""
        # Create a temporary directory to act as the project root
        root = tmp_path / "test_project"
        root.mkdir()

        # Call the setup function
        setup_project_structure.setup_directories(root)

        # Verify that all expected directories exist
        expected_dirs = [
            "src",
            "src/lib",
            "src/services",
            "src/analysis",
            "src/cli",
            "src/models",
            "src/scripts",
            "tests",
            "tests/unit",
            "tests/integration",
            "data",
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "artifacts",
            "specs",
            "specs/001-gene-regulation",
            "specs/001-gene-regulation/contracts",
            "config",
        ]

        for dir_name in expected_dirs:
            dir_path = root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

    def test_setup_directories_idempotent(self, tmp_path):
        """Verify that running setup_directories multiple times does not cause errors."""
        root = tmp_path / "test_project_idempotent"
        root.mkdir()

        # Run setup twice
        setup_project_structure.setup_directories(root)
        setup_project_structure.setup_directories(root)

        # Verify structure still exists
        assert (root / "src").exists()
        assert (root / "data/raw").exists()
        assert (root / "specs/001-gene-regulation/contracts").exists()