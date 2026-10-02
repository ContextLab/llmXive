import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import get_project_root
from setup_directories import main as setup_main

class TestT008Integration:
    """Integration tests for T008 directory setup."""

    def test_main_function_execution(self):
        """Test that the main function executes without errors."""
        project_root = get_project_root()
        
        # Run the main function
        exit_code = setup_main()
        
        # Should exit with 0
        assert exit_code == 0, f"Main function exited with code {exit_code}"

    def test_full_directory_tree_created(self):
        """Verify the complete directory tree structure is created."""
        project_root = get_project_root()
        
        # Check all required paths
        required_paths = [
            "data/raw/.gitkeep",
            "data/processed/.gitkeep",
            "results/.gitkeep",
        ]
        
        for rel_path in required_paths:
            full_path = project_root / rel_path
            assert full_path.exists(), f"Path {full_path} does not exist"
            assert full_path.is_file() if ".gitkeep" in rel_path else full_path.is_dir(), \
                f"Path {full_path} is not the expected type"

    def test_directories_are_writable(self):
        """Verify that the created directories are writable."""
        project_root = get_project_root()
        
        test_dirs = [
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "results",
        ]
        
        for test_dir in test_dirs:
            # Try to create a temporary file
            test_file = test_dir / ".test_write_permission"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                pytest.fail(f"Directory {test_dir} is not writable: {e}")