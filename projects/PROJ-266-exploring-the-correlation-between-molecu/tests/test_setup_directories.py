import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.config import get_project_root
from data.setup_directories import create_directories, verify_directories

class TestDirectorySetup:
    """
    Unit tests for directory creation and verification logic.
    """

    def test_create_directories_creates_all_required_dirs(self):
        """
        Test that create_directories creates data/raw, data/processed,
        state/projects, and state/pending.
        """
        project_root = get_project_root()
        
        # Define expected directories
        expected_dirs = [
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "state" / "projects",
            project_root / "state" / "pending",
        ]
        
        # Ensure they don't exist before test (optional cleanup)
        for d in expected_dirs:
            if d.exists():
                # Don't remove, just verify they are created
                pass
        
        # Run the creation function
        create_directories(project_root)
        
        # Verify all directories were created
        for expected_dir in expected_dirs:
            assert expected_dir.exists(), f"Directory was not created: {expected_dir}"
            assert expected_dir.is_dir(), f"Path is not a directory: {expected_dir}"

    def test_verify_directories_raises_on_missing(self, tmp_path):
        """
        Test that verify_directories raises FileNotFoundError if a directory is missing.
        """
        # Create a temporary project root with only some directories
        missing_dir = tmp_path / "data" / "raw"
        # Do not create missing_dir
        
        with pytest.raises(FileNotFoundError):
            # We need to mock the project root or pass a specific path
            # Since verify_directories expects a Path, we pass tmp_path
            # But verify_directories looks for specific relative paths
            # So we construct the full path for the missing one to trigger the error
            # Actually, verify_directories iterates over specific relative paths
            # Let's create the other dirs but not the one we want to test
            (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
            (tmp_path / "state" / "projects").mkdir(parents=True, exist_ok=True)
            (tmp_path / "state" / "pending").mkdir(parents=True, exist_ok=True)
            
            # Now verify should fail because data/raw is missing
            verify_directories(tmp_path)

    def test_verify_directories_passes_when_all_exist(self, tmp_path):
        """
        Test that verify_directories passes when all required directories exist.
        """
        project_root = tmp_path
        
        # Create all required directories
        create_directories(project_root)
        
        # This should not raise any exception
        verify_directories(project_root)
        
        # If we get here, the test passed
        assert True
