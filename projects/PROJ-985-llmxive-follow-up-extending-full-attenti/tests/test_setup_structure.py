"""
Unit tests for project structure setup verification.
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import setup module
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_project_structure import create_directories, verify_structure, REQUIRED_DIRS

class TestProjectStructure:
    def test_required_dirs_defined(self):
        """Test that required directories are defined."""
        assert len(REQUIRED_DIRS) == 10
        assert "code" in REQUIRED_DIRS
        assert "tests" in REQUIRED_DIRS
        assert "data" in REQUIRED_DIRS

    def test_create_directories_creates_all(self, tmp_path):
        """Test that create_directories creates all required directories."""
        created = create_directories(tmp_path)
        for dir_name in REQUIRED_DIRS:
            assert (tmp_path / dir_name).exists()
            assert (tmp_path / dir_name).is_dir()

    def test_verify_structure_all_present(self, tmp_path):
        """Test verify_structure when all directories exist."""
        # First create them
        create_directories(tmp_path)
        
        success, missing = verify_structure(tmp_path)
        assert success is True
        assert len(missing) == 0
        
        # Check that verification log was created
        log_path = tmp_path / "data" / "logs" / "structure_verification.txt"
        assert log_path.exists()

    def test_verify_structure_missing_dirs(self, tmp_path):
        """Test verify_structure when some directories are missing."""
        # Don't create any directories
        success, missing = verify_structure(tmp_path)
        assert success is False
        assert len(missing) == len(REQUIRED_DIRS)
        assert "code" in missing

    def test_verification_log_content(self, tmp_path):
        """Test that verification log contains expected content."""
        create_directories(tmp_path)
        success, missing = verify_structure(tmp_path)
        
        log_path = tmp_path / "data" / "logs" / "structure_verification.txt"
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "Project Structure Verification Report" in content
        assert "VERIFICATION PASSED" in content
        assert "code" in content
        assert "tests" in content
        assert "data" in content