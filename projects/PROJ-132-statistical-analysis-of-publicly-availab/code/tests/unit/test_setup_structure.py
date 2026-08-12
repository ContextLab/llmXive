"""
Unit tests for project structure creation (T002a).
Verifies that all required directories exist after setup.
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.setup_project import create_directories


class TestProjectStructure:
    """Test cases for project structure creation."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up a temporary directory for testing."""
        self.tmp_path = tmp_path
        # Change to temp directory for testing
        self.original_cwd = Path.cwd()
        os.chdir(self.tmp_path)
        
        # Create src and data directories structure to match project layout
        (self.tmp_path / "src").mkdir()
        (self.tmp_path / "data").mkdir()
        (self.tmp_path / "tests").mkdir()
        
        yield
        
        # Restore original directory
        os.chdir(self.original_cwd)

    def test_create_directories_returns_list(self):
        """Test that create_directories returns a list of paths."""
        result = create_directories()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_all_required_directories_created(self):
        """Test that all required directories are created."""
        required_dirs = [
            "src/data",
            "src/models",
            "src/analysis",
            "src/utils",
            "src/cli",
            "data/raw",
            "data/processed",
            "data/interim",
            "tests/contract",
            "tests/unit",
            "tests/integration",
            "docs"
        ]
        
        create_directories()
        
        for dir_path in required_dirs:
            full_path = self.tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_directory_structure_matches_spec(self):
        """Test that the directory structure matches the task specification."""
        expected_structure = {
            "src": {"data", "models", "analysis", "utils", "cli"},
            "data": {"raw", "processed", "interim"},
            "tests": {"contract", "unit", "integration"},
            "docs": set()
        }
        
        create_directories()
        
        for parent, children in expected_structure.items():
            parent_path = self.tmp_path / parent
            assert parent_path.exists(), f"Parent directory {parent} does not exist"
            
            for child in children:
                child_path = parent_path / child
                assert child_path.exists(), f"Child directory {parent}/{child} does not exist"
                assert child_path.is_dir(), f"{parent}/{child} is not a directory"

    def test_existent_directory_handling(self):
        """Test that existing directories are handled gracefully."""
        # Create directories manually first
        create_directories()
        
        # Run again - should not raise error
        result = create_directories()
        assert len(result) > 0

    def test_nested_directory_creation(self):
        """Test that nested directories are created properly."""
        # Remove a nested directory and test recreation
        nested_dir = self.tmp_path / "data" / "raw"
        if nested_dir.exists():
            import shutil
            shutil.rmtree(nested_dir)
        
        create_directories()
        
        assert nested_dir.exists(), "Nested directory was not recreated"
        assert nested_dir.is_dir(), "Nested path is not a directory"