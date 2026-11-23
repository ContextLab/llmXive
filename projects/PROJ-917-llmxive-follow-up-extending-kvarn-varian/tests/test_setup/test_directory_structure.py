import pytest
import os
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directory_structure import get_project_root, create_directories, verify_structure

class TestDirectoryStructure:
    """
    Tests for the directory structure initialization functionality.
    
    These tests verify that:
    1. The project root is correctly identified
    2. All required directories are created
    3. The structure can be verified
    """

    def test_project_root_identification(self):
        """Test that the project root is correctly identified."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        # Verify we can find the code directory
        assert (root / "code").exists()

    def test_create_directories(self, tmp_path):
        """Test that create_directories creates all required subdirectories."""
        # Create a temporary project root
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        
        # Create the expected directory structure
        result = create_directories(test_root)
        
        assert result is True
        
        # Verify key directories exist
        assert (test_root / "code").is_dir()
        assert (test_root / "data").is_dir()
        assert (test_root / "tests").is_dir()
        assert (test_root / "code" / "data_generation").is_dir()
        assert (test_root / "code" / "model_training").is_dir()
        assert (test_root / "code" / "simulation").is_dir()
        assert (test_root / "code" / "analysis").is_dir()
        assert (test_root / "data" / "raw").is_dir()
        assert (test_root / "data" / "processed").is_dir()
        assert (test_root / "data" / "models").is_dir()
        assert (test_root / "data" / "simulation").is_dir()
        assert (test_root / "data" / "analysis").is_dir()
        assert (test_root / "state" / "projects").is_dir()

    def test_verify_structure(self, tmp_path):
        """Test that verify_structure correctly validates the directory tree."""
        # Create a test project with full structure
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        
        # First create the directories
        create_directories(test_root)
        
        # Then verify
        result = verify_structure(test_root)
        assert result is True

    def test_verify_structure_missing_dir(self, tmp_path):
        """Test that verify_structure returns False when a directory is missing."""
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        
        # Create only partial structure
        (test_root / "code").mkdir()
        # Missing data, tests, etc.
        
        result = verify_structure(test_root)
        assert result is False

    def test_idempotent_creation(self, tmp_path):
        """Test that creating directories twice doesn't cause errors."""
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        
        # Create directories twice
        result1 = create_directories(test_root)
        result2 = create_directories(test_root)
        
        assert result1 is True
        assert result2 is True