"""
Unit tests for the setup_directories module.
Verifies that directory creation functions work correctly.
"""
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, 'code')
from setup_directories import ensure_dir, DIRECTORIES


class TestEnsureDir:
    """Test cases for the ensure_dir function."""
    
    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory that doesn't exist."""
        new_dir = tmp_path / "new_test_dir"
        result = ensure_dir(str(new_dir))
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_existing_directory(self, tmp_path):
        """Test that existing directory returns True without error."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        
        result = ensure_dir(str(existing_dir))
        
        assert result is True
        assert existing_dir.exists()
    
    def test_nested_directories(self, tmp_path):
        """Test creating nested directories that don't exist."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        result = ensure_dir(str(nested_dir))
        
        assert result is True
        assert nested_dir.exists()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()
    
    def test_invalid_path_permissions(self, tmp_path):
        """Test handling of path with permission issues (if applicable)."""
        # Create a file where we want a directory
        file_path = tmp_path / "file_instead_of_dir"
        file_path.touch()
        
        # This should fail because a file exists at that path
        result = ensure_dir(str(file_path))
        
        # The function should return False for this case
        assert result is False


class TestDirectoriesList:
    """Test cases for the DIRECTORIES constant."""
    
    def test_directories_list_not_empty(self):
        """Test that the DIRECTORIES list is not empty."""
        assert len(DIRECTORIES) > 0
    
    def test_directories_list_has_required_entries(self):
        """Test that all required directories are in the list."""
        required = ["code", "data", "results", "tests", "data/raw", "data/processed"]
        
        for req_dir in required:
            assert req_dir in DIRECTORIES, f"Required directory {req_dir} not found in DIRECTORIES"
    
    def test_no_duplicate_entries(self):
        """Test that there are no duplicate directory entries."""
        assert len(DIRECTORIES) == len(set(DIRECTORIES)), "Duplicate entries found in DIRECTORIES"


class TestSetupIntegration:
    """Integration tests for the setup process."""
    
    def test_all_directories_created_in_temp(self, tmp_path):
        """Test that all directories can be created in a temporary location."""
        with patch('setup_directories.os.getcwd', return_value=str(tmp_path)):
            success_count = 0
            failure_count = 0
            
            for dir_path in DIRECTORIES:
                full_path = tmp_path / dir_path
                try:
                    os.makedirs(full_path, exist_ok=True)
                    success_count += 1
                except Exception:
                    failure_count += 1
            
            assert failure_count == 0, f"Failed to create {failure_count} directories"
            assert success_count == len(DIRECTORIES)
    
    def test_directory_structure_exists(self, tmp_path):
        """Test that the expected directory structure is created."""
        # Create a temporary directory to act as project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Change to project root for testing
        original_cwd = os.getcwd()
        try:
            os.chdir(str(project_root))
            
            # Create all directories
            for dir_path in DIRECTORIES:
                ensure_dir(dir_path)
            
            # Verify key directories exist
            assert (project_root / "data").exists()
            assert (project_root / "data" / "raw").exists()
            assert (project_root / "data" / "processed").exists()
            assert (project_root / "results").exists()
            assert (project_root / "results" / "statistics").exists()
            assert (project_root / "tests").exists()
            assert (project_root / "code").exists()
            
        finally:
            os.chdir(original_cwd)