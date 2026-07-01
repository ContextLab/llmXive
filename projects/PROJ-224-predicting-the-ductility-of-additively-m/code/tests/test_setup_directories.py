import pytest
from pathlib import Path
import sys
import os
from setup_directories import create_directories

class TestDirectoryCreation:
    """Tests for the directory creation functionality."""

    def test_create_directories_returns_true(self):
        """Test that create_directories returns True on success."""
        # Note: This test assumes the directories can be created
        # In a real CI environment, we might need to clean up after this test
        result = create_directories()
        assert result is True

    def test_code_data_exists(self):
        """Test that code/data/ directory exists after creation."""
        # Get the project root (parent of code directory)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        # Run the creation function
        create_directories()
        
        # Check if the directory exists
        data_dir = project_root / "code" / "data"
        assert data_dir.exists(), f"Directory {data_dir} does not exist"
        assert data_dir.is_dir(), f"{data_dir} is not a directory"

    def test_code_models_exists(self):
        """Test that code/models/ directory exists after creation."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        create_directories()
        
        models_dir = project_root / "code" / "models"
        assert models_dir.exists(), f"Directory {models_dir} does not exist"
        assert models_dir.is_dir(), f"{models_dir} is not a directory"

    def test_code_analysis_exists(self):
        """Test that code/analysis/ directory exists after creation."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        create_directories()
        
        analysis_dir = project_root / "code" / "analysis"
        assert analysis_dir.exists(), f"Directory {analysis_dir} does not exist"
        assert analysis_dir.is_dir(), f"{analysis_dir} is not a directory"

    def test_all_directories_exist(self):
        """Test that all required subdirectories exist after creation."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        create_directories()
        
        required_dirs = [
            "code/data",
            "code/models",
            "code/analysis"
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Required directory {full_path} does not exist"
            assert full_path.is_dir(), f"{full_path} is not a directory"