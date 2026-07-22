"""
Tests for directory verification logic.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# Note: We need to mock the config.get_project_root to use a temp directory
from unittest.mock import patch
from code.verify_directories import verify_directories

class TestVerifyDirectories:
    
    def test_verify_directories_all_present(self, tmp_path):
        """Test that verification passes when all directories exist."""
        # Create a temporary project structure
        dirs_to_create = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests",
            "state/projects",
            "code/models"
        ]
        
        for d in dirs_to_create:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        
        # Mock get_project_root to return our temp path
        with patch('code.verify_directories.get_project_root', return_value=str(tmp_path)):
            result = verify_directories()
            assert result is True

    def test_verify_directories_missing_one(self, tmp_path):
        """Test that verification fails when one directory is missing."""
        # Create most directories but omit one
        dirs_to_create = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests",
            "state/projects"
            # Missing "code/models"
        ]
        
        for d in dirs_to_create:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        
        with patch('code.verify_directories.get_project_root', return_value=str(tmp_path)):
            result = verify_directories()
            assert result is False

    def test_verify_directories_missing_all(self, tmp_path):
        """Test that verification fails when no directories exist."""
        with patch('code.verify_directories.get_project_root', return_value=str(tmp_path)):
            result = verify_directories()
            assert result is False
