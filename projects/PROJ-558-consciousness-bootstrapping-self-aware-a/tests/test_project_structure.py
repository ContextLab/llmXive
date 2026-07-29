import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to import the script
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from create_project_structure import create_structure

class TestProjectStructure:
    """Tests for T001a: Create directory structure."""

    def test_create_structure_executes(self):
        """Test that the create_structure function runs without error."""
        # This test ensures the function can be called
        # The actual directory creation is side-effect based
        result = create_structure()
        assert isinstance(result, list)

    def test_required_directories_exist(self):
        """Verify that all required directories exist after creation."""
        base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
        
        required_paths = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts/checkpoints",
            "artifacts/results"
        ]
        
        for rel_path in required_paths:
            full_path = base_dir / rel_path
            assert full_path.exists(), f"Directory missing: {full_path}"
            assert full_path.is_dir(), f"Not a directory: {full_path}"

    def test_directory_hierarchy(self):
        """Verify the correct hierarchy is created."""
        base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
        
        # Check that data/raw exists and is inside data
        assert (base_dir / "data").exists()
        assert (base_dir / "data" / "raw").exists()
        
        # Check that artifacts/checkpoints exists and is inside artifacts
        assert (base_dir / "artifacts").exists()
        assert (base_dir / "artifacts" / "checkpoints").exists()
        assert (base_dir / "artifacts" / "results").exists()

    def test_project_root_exists(self):
        """Verify the main project root directory exists."""
        base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
        assert base_dir.exists()
        assert base_dir.is_dir()