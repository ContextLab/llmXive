"""
Unit tests for manual validation directory structure setup.

Tests verify that:
1. Directory creation succeeds
2. All expected directories exist after creation
3. Directories are actually directories (not files)
4. Script returns appropriate exit codes
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.audit.manual_validation_setup import (
    MANUAL_VALIDATION_DIRS,
    create_directory_structure,
    verify_directory_structure,
)


class TestManualValidationSetup:
    """Test cases for manual validation directory setup."""

    def test_create_directory_structure_creates_all_dirs(self, tmp_path):
        """Verify that all manual validation directories are created."""
        success, created_paths = create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        
        assert success is True, "Directory creation should succeed"
        assert len(created_paths) == len(MANUAL_VALIDATION_DIRS), (
            f"Expected {len(MANUAL_VALIDATION_DIRS)} directories, got {len(created_paths)}"
        )

    def test_verify_directory_structure_confirms_all_exist(self, tmp_path):
        """Verify that directory verification confirms all created directories."""
        # First create the directories
        create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        
        # Then verify them
        success, verified_paths = verify_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        
        assert success is True, "Directory verification should succeed"
        assert len(verified_paths) == len(MANUAL_VALIDATION_DIRS), (
            f"Expected {len(MANUAL_VALIDATION_DIRS)} verified paths, got {len(verified_paths)}"
        )

    def test_all_created_paths_are_directories(self, tmp_path):
        """Verify that all created paths are actually directories."""
        _, created_paths = create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        
        for path in created_paths:
            assert path.is_dir(), f"Path {path} should be a directory"

    def test_main_directory_structure_exists(self, tmp_path):
        """Verify the main manual_validation directory exists."""
        success, created_paths = create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        
        main_dir = tmp_path / "data/manual_validation"
        assert main_dir.exists(), "Main manual_validation directory should exist"
        assert main_dir.is_dir(), "Main manual_validation should be a directory"

    def test_subdirectory_structure(self, tmp_path):
        """Verify all subdirectories are created under manual_validation."""
        success, created_paths = create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        
        expected_subdirs = ["raw", "annotations", "processed", "provenance"]
        main_dir = tmp_path / "data/manual_validation"
        
        for subdir in expected_subdirs:
            subdir_path = main_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir} should exist"
            assert subdir_path.is_dir(), f"Subdirectory {subdir} should be a directory"

    def test_create_with_existing_dirs(self, tmp_path):
        """Verify that creating directories that already exist succeeds."""
        # Create directories first time
        success1, _ = create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        assert success1 is True, "First creation should succeed"
        
        # Create directories second time (should not fail)
        success2, _ = create_directory_structure(tmp_path, MANUAL_VALIDATION_DIRS)
        assert success2 is True, "Second creation should succeed (exist_ok=True)"

    def test_empty_dir_list(self, tmp_path):
        """Verify behavior with empty directory list."""
        success, created_paths = create_directory_structure(tmp_path, [])
        
        assert success is True, "Empty directory list should succeed"
        assert len(created_paths) == 0, "No paths should be created"

    def test_manual_validation_dirs_constant(self):
        """Verify MANUAL_VALIDATION_DIRS constant is properly defined."""
        assert isinstance(MANUAL_VALIDATION_DIRS, list), "MANUAL_VALIDATION_DIRS should be a list"
        assert len(MANUAL_VALIDATION_DIRS) > 0, "MANUAL_VALIDATION_DIRS should not be empty"
        assert "data/manual_validation" in MANUAL_VALIDATION_DIRS, (
            "Main manual_validation directory should be in list"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
