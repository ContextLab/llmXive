"""
Unit tests for setup_data_dirs.py
Verifies that data directories are created and are writable.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories, get_project_root

class TestSetupDataDirs:
    def test_creates_data_structure_in_temp(self, tmp_path):
        """
        Test that the function creates data/raw and data/processed 
        inside a temporary directory.
        """
        # Create a temporary project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        dirs = setup_data_directories(project_root)

        data_root = project_root / "data"
        raw_dir = data_root / "raw"
        processed_dir = data_root / "processed"

        assert data_root.exists(), "data/ directory should exist"
        assert raw_dir.exists(), "data/raw/ directory should exist"
        assert processed_dir.exists(), "data/processed/ directory should exist"
        assert data_root in dirs
        assert raw_dir in dirs
        assert processed_dir in dirs

    def test_writability_verified(self, tmp_path):
        """
        Test that the function verifies writability by creating/deleting a test file.
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Mock a read-only scenario would raise an error, but here we test success path
        # The function itself attempts to touch and unlink a file.
        # We verify that no exception is raised and directories are returned.
        dirs = setup_data_directories(project_root)
        
        assert len(dirs) == 3, "Should return 3 verified directories"

    def test_handles_existing_directories(self, tmp_path):
        """
        Test that the function handles pre-existing directories gracefully.
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Pre-create the structure
        (project_root / "data" / "raw").mkdir(parents=True)
        (project_root / "data" / "processed").mkdir(parents=True)

        # Should not raise and should verify them
        dirs = setup_data_directories(project_root)
        
        assert len(dirs) == 3

    def test_raises_on_unwritable(self, tmp_path):
        """
        Test that the function raises RuntimeError if a directory is not writable.
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        data_dir = project_root / "data"
        data_dir.mkdir()
        
        # Make data_dir read-only (if running as non-root)
        if os.geteuid() != 0:
            data_dir.chmod(0o555)
            
            try:
                with pytest.raises(RuntimeError):
                    setup_data_directories(project_root)
            finally:
                # Restore permissions for cleanup
                data_dir.chmod(0o755)
        else:
            # Root can write anywhere, so skip this specific check in this env
            # Just verify it doesn't crash on creation
            setup_data_directories(project_root)