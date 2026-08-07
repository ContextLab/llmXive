"""
Unit tests for the directory creation script (T008a).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(code_dir))

from data.setup_directories import create_directories, get_project_root, DATA_DIR, RAW_DIR, PROCESSED_DIR

class TestDirectoryCreation:
    """Tests for directory creation functionality."""

    def test_project_root_detection(self):
        """Test that project root is detected correctly."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_raw_directory_exists(self):
        """Test that data/raw directory exists after creation."""
        # Ensure directory exists
        create_directories()
        assert os.path.isdir(RAW_DIR), f"Expected directory {RAW_DIR} to exist"

    def test_processed_directory_exists(self):
        """Test that data/processed directory exists after creation."""
        # Ensure directory exists
        create_directories()
        assert os.path.isdir(PROCESSED_DIR), f"Expected directory {PROCESSED_DIR} to exist"

    def test_create_directories_idempotent(self):
        """Test that creating directories multiple times doesn't fail."""
        result1 = create_directories()
        result2 = create_directories()
        assert result1 is True
        assert result2 is True

    def test_directory_structure(self):
        """Test the full directory structure is created."""
        create_directories()
        
        # Check parent directory exists
        assert os.path.isdir(DATA_DIR), f"Expected {DATA_DIR} to exist"
        
        # Check children exist
        assert os.path.isdir(RAW_DIR), f"Expected {RAW_DIR} to exist"
        assert os.path.isdir(PROCESSED_DIR), f"Expected {PROCESSED_DIR} to exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])