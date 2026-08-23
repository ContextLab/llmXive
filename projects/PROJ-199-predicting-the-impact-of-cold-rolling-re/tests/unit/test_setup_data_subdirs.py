"""
Unit tests for T005: setup_data_subdirs.py

Tests verify that the script correctly creates the required directory structure
and .gitkeep files, and that the verification function works as expected.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure we can import from the code package
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.setup_data_subdirs import create_subdirectories, verify_subdirectories

class TestDataSubdirs:
    """Test suite for data subdirectory setup."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory to simulate the data folder."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup after test
        shutil.rmtree(temp_dir)

    def test_create_subdirectories_creates_dirs(self, temp_data_dir):
        """Test that create_subdirectories creates the specified directories."""
        subdirs = ["raw", "processed", "interim"]
        
        create_subdirectories(temp_data_dir, subdirs)
        
        for subdir_name in subdirs:
            subdir_path = temp_data_dir / subdir_name
            assert subdir_path.is_dir(), f"Directory {subdir_path} was not created."

    def test_create_subdirectories_creates_gitkeep(self, temp_data_dir):
        """Test that create_subdirectories creates .gitkeep in each directory."""
        subdirs = ["raw", "processed", "interim"]
        
        create_subdirectories(temp_data_dir, subdirs)
        
        for subdir_name in subdirs:
            subdir_path = temp_data_dir / subdir_name
            gitkeep_path = subdir_path / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep not found in {subdir_path}"
            assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

    def test_verify_subdirectories_success(self, temp_data_dir):
        """Test that verify_subdirectories returns True when structure is correct."""
        subdirs = ["raw", "processed", "interim"]
        
        # Create the structure first
        create_subdirectories(temp_data_dir, subdirs)
        
        # Verify
        result = verify_subdirectories(temp_data_dir, subdirs)
        assert result is True, "Verification should pass for correct structure."

    def test_verify_subdirectories_missing_dir(self, temp_data_dir):
        """Test that verify_subdirectories returns False when a directory is missing."""
        subdirs = ["raw", "processed", "interim"]
        
        # Create only 'raw'
        (temp_data_dir / "raw").mkdir()
        (temp_data_dir / "raw" / ".gitkeep").touch()
        
        # Verify should fail for 'processed' and 'interim'
        result = verify_subdirectories(temp_data_dir, subdirs)
        assert result is False, "Verification should fail when directories are missing."

    def test_verify_subdirectories_missing_gitkeep(self, temp_data_dir):
        """Test that verify_subdirectories returns False when .gitkeep is missing."""
        subdirs = ["raw", "processed"]
        
        # Create 'raw' with .gitkeep
        (temp_data_dir / "raw").mkdir()
        (temp_data_dir / "raw" / ".gitkeep").touch()
        
        # Create 'processed' WITHOUT .gitkeep
        (temp_data_dir / "processed").mkdir()
        
        result = verify_subdirectories(temp_data_dir, subdirs)
        assert result is False, "Verification should fail when .gitkeep is missing."

    def test_idempotency(self, temp_data_dir):
        """Test that running create_subdirectories multiple times is safe."""
        subdirs = ["raw", "processed"]
        
        # Run twice
        create_subdirectories(temp_data_dir, subdirs)
        create_subdirectories(temp_data_dir, subdirs)
        
        # Verify structure is still correct
        result = verify_subdirectories(temp_data_dir, subdirs)
        assert result is True, "Structure should be valid after multiple runs."