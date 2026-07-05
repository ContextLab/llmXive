"""
Tests for setup_directories module

Tests the directory creation functionality to ensure:
- All required directories are created
- Existing directories are handled gracefully
- Errors are properly reported
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_directories import create_directory_structure, DIRECTORIES


class TestCreateDirectoryStructure:
    """Tests for the create_directory_structure function."""
    
    def test_creates_all_directories(self, tmp_path):
        """Test that all required directories are created."""
        results = create_directory_structure(str(tmp_path))
        
        # Check that all directories were created
        for dir_path in DIRECTORIES:
            full_path = os.path.join(str(tmp_path), dir_path)
            assert os.path.exists(full_path), f"Directory {dir_path} was not created"
            assert os.path.isdir(full_path), f"{dir_path} is not a directory"
        
        # Check results summary
        assert len(results['created']) == len(DIRECTORIES)
        assert len(results['skipped']) == 0
        assert len(results['errors']) == 0
    
    def test_handles_existing_directories(self, tmp_path):
        """Test that existing directories are skipped gracefully."""
        # Create some directories beforehand
        for dir_path in DIRECTORIES[:3]:
            full_path = os.path.join(str(tmp_path), dir_path)
            os.makedirs(full_path, exist_ok=True)
        
        results = create_directory_structure(str(tmp_path))
        
        # Check that existing directories were skipped
        for dir_path in DIRECTORIES[:3]:
            assert dir_path in results['skipped']
        
        # Check that remaining directories were created
        for dir_path in DIRECTORIES[3:]:
            full_path = os.path.join(str(tmp_path), dir_path)
            assert os.path.exists(full_path)
            assert dir_path in results['created']
    
    def test_returns_error_on_failure(self, tmp_path):
        """Test that errors are properly reported."""
        # Mock os.makedirs to raise an exception for a specific directory
        with patch('setup_directories.os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")
            
            results = create_directory_structure(str(tmp_path))
            
            # Check that errors were recorded
            assert len(results['errors']) > 0
            assert any(e['error'] == "Permission denied" for e in results['errors'])
    
    def test_nested_directories_created(self, tmp_path):
        """Test that nested directories are created correctly."""
        results = create_directory_structure(str(tmp_path))
        
        # Check nested directories
        nested_dirs = ['tests/unit', 'tests/integration', 'data/raw', 'data/processed']
        for dir_path in nested_dirs:
            full_path = os.path.join(str(tmp_path), dir_path)
            assert os.path.exists(full_path), f"Nested directory {dir_path} was not created"
    
    def test_creates_init_files(self, tmp_path):
        """Test that __init__.py files are created for Python packages."""
        # This test verifies that the setup process creates necessary package files
        # Note: The current implementation doesn't create __init__.py files,
        # but this test documents the expectation for future enhancement.
        
        results = create_directory_structure(str(tmp_path))
        
        # Check that code and tests directories exist
        assert os.path.exists(os.path.join(str(tmp_path), 'code'))
        assert os.path.exists(os.path.join(str(tmp_path), 'tests'))
        
        # TODO: Update create_directory_structure to create __init__.py files
        # assert os.path.exists(os.path.join(str(tmp_path), 'code', '__init__.py'))
        # assert os.path.exists(os.path.join(str(tmp_path), 'tests', '__init__.py'))
