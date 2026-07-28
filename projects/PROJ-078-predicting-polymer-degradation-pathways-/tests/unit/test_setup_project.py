"""
Unit tests for the project setup module (setup_project.py).
Verifies T001a implementation.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We assume the test runner adds 'code' to sys.path or we run from the root
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_project import create_directories, verify_directories, REQUIRED_DIRS
from utils import setup_logging

# Setup logging for tests
setup_logging(level="DEBUG")

class TestCreateDirectories:
    def test_creates_all_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Act
        created = create_directories(base_path=tmp_path)
        
        # Assert
        assert len(created) == len(REQUIRED_DIRS)
        for dir_name in REQUIRED_DIRS:
            assert (tmp_path / dir_name).exists()
            assert (tmp_path / dir_name).is_dir()

    def test_skips_existing_directories(self, tmp_path):
        """Test that existing directories are not recreated."""
        # Arrange: Pre-create one directory
        existing_dir = tmp_path / "code"
        existing_dir.mkdir()
        
        # Act
        created = create_directories(base_path=tmp_path)
        
        # Assert: Only the new ones should be in the returned list
        # (The implementation logs but doesn't add to 'created' if it exists)
        assert len(created) == len(REQUIRED_DIRS) - 1
        assert existing_dir not in created

    def test_handles_nested_directories(self, tmp_path):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        # Act
        created = create_directories(base_path=tmp_path)
        
        # Assert
        nested_path = tmp_path / "data" / "raw"
        assert nested_path.exists()
        assert nested_path.is_dir()

    def test_raises_on_permission_error(self, tmp_path):
        """Test that an error is raised if directory creation fails."""
        # Mock the mkdir to raise an OSError
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                create_directories(base_path=tmp_path)

class TestVerifyDirectories:
    def test_returns_true_when_all_exist(self, tmp_path):
        """Test that verify returns True when all directories exist."""
        # Arrange: Create all directories
        create_directories(base_path=tmp_path)
        
        # Act
        result = verify_directories(base_path=tmp_path)
        
        # Assert
        assert result is True

    def test_returns_false_when_missing(self, tmp_path):
        """Test that verify returns False when a directory is missing."""
        # Arrange: Create only some directories
        (tmp_path / "code").mkdir()
        
        # Act
        result = verify_directories(base_path=tmp_path)
        
        # Assert
        assert result is False

    def test_returns_false_when_file_instead_of_dir(self, tmp_path):
        """Test that verify returns False if a path exists but is a file."""
        # Arrange: Create a file instead of a directory
        file_path = tmp_path / "code"
        file_path.touch()
        
        # Act
        result = verify_directories(base_path=tmp_path)
        
        # Assert
        assert result is False
