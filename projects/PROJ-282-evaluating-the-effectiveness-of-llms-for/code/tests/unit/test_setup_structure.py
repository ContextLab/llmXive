import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# Adjust import path based on where setup_project_structure.py is located
# It is in code/setup_project_structure.py, so we import from the parent of code
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project_structure import create_structure

class TestProjectStructureCreation:
    @pytest.fixture
    def temp_root(self):
        """Create a temporary directory to act as project root."""
        tmp_dir = tempfile.mkdtemp()
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_creates_all_required_dirs(self, temp_root):
        """Test that create_structure creates all required directories."""
        create_structure(temp_root)

        required_paths = [
            "code/src",
            "code/tests",
            "data/raw",
            "data/processed",
            "data/results",
            "data/logs",
            "state",
            "contracts",
            "specs",
            "figures"
        ]

        for rel_path in required_paths:
            full_path = temp_root / rel_path
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} is not a directory."

    def test_creates_gitkeep_files(self, temp_root):
        """Test that .gitkeep files are created in new directories."""
        create_structure(temp_root)

        required_paths = [
            "code/src",
            "code/tests",
            "data/raw",
            "data/processed",
            "data/results",
            "data/logs",
            "state",
            "contracts",
            "specs",
            "figures"
        ]

        for rel_path in required_paths:
            gitkeep = temp_root / rel_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep not found in {temp_root / rel_path}"

    def test_idempotent_creation(self, temp_root):
        """Test that running create_structure twice does not fail."""
        # First run
        create_structure(temp_root)
        
        # Second run should not raise exceptions
        create_structure(temp_root)

        # Verify structure still exists
        assert (temp_root / "code/src").exists()