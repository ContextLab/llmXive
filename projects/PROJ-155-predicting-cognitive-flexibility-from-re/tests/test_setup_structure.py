"""
Tests for project structure setup.

These tests verify that the project directory structure is created correctly
and that the verification functions work as expected.
"""
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from setup_structure import get_project_root, ensure_dir, create_project_structure, verify_structure

class TestProjectStructure:
    """Test cases for project structure utilities."""
    
    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test that ensure_dir creates a directory if it doesn't exist."""
        test_dir = tmp_path / "new_dir"
        assert not test_dir.exists()
        
        ensure_dir(str(test_dir))
        
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_ensure_dir_skips_existing_directory(self, tmp_path):
        """Test that ensure_dir does nothing if directory already exists."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        assert test_dir.exists()
        
        ensure_dir(str(test_dir))
        
        # Should still exist and not raise
        assert test_dir.exists()
    
    def test_create_project_structure_creates_all_dirs(self, tmp_path):
        """Test that create_project_structure creates all required directories."""
        # Mock get_project_root to return our temp directory
        with patch('setup_structure.get_project_root', return_value=str(tmp_path)):
            created = create_project_structure()
            
            required_dirs = ['code', 'data', 'docs', 'tests']
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
    
    def test_verify_structure_returns_true_when_all_exist(self, tmp_path):
        """Test that verify_structure returns True when all dirs exist."""
        # Create the required directories
        for dir_name in ['code', 'data', 'docs', 'tests']:
            (tmp_path / dir_name).mkdir()
        
        with patch('setup_structure.get_project_root', return_value=str(tmp_path)):
            result = verify_structure()
            assert result is True
    
    def test_verify_structure_returns_false_when_missing(self, tmp_path):
        """Test that verify_structure returns False when some dirs are missing."""
        # Create only some directories
        (tmp_path / 'code').mkdir()
        (tmp_path / 'data').mkdir()
        # Missing 'docs' and 'tests'
        
        with patch('setup_structure.get_project_root', return_value=str(tmp_path)):
            result = verify_structure()
            assert result is False
    
    def test_get_project_root_returns_parent_of_code(self):
        """Test that get_project_root correctly identifies the project root."""
        # This test assumes the standard layout where this file is in tests/
        # and code/ is a sibling
        project_root = get_project_root()
        
        # Should be a valid directory
        assert os.path.isdir(project_root)
        
        # Should contain 'code' directory (or at least be the parent)
        assert os.path.basename(os.path.dirname(__file__)) == 'tests'
        # The parent of 'tests' should be the project root
        expected_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assert project_root == expected_root
