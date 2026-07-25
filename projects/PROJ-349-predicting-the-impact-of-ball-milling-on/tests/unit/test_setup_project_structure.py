import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from setup_project_structure import setup_directories

class TestSetupProjectStructure:
    """
    Unit tests for the project structure setup script.
    Verifies that the required directories are created and .gitkeep files are placed.
    """

    def test_setup_directories_creates_all_folders(self, tmp_path):
        """
        Test that setup_directories creates all required directories.
        """
        # Change to the temp directory to simulate project root
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Call the function
            result = setup_directories()
            
            # Assert success
            assert result is True
            
            # Define expected directories
            expected_dirs = [
                "src",
                "tests",
                "data/raw",
                "data/processed",
                "data/splits",
                "results",
                "contracts",
                ".github/workflows",
                "data/fallback",
                "figures"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
                # Verify .gitkeep exists
                keep_file = dir_path / ".gitkeep"
                assert keep_file.exists(), f".gitkeep missing in {dir_name}"
                
        finally:
            # Restore original directory
            os.chdir(original_dir)

    def test_setup_directories_idempotent(self, tmp_path):
        """
        Test that running setup_directories twice does not cause errors.
        """
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run twice
            result1 = setup_directories()
            result2 = setup_directories()
            
            assert result1 is True
            assert result2 is True
            
            # Verify structure still intact
            assert (tmp_path / "src").exists()
            assert (tmp_path / "data/raw").exists()
            
        finally:
            os.chdir(original_dir)

    def test_setup_directories_nested_creation(self, tmp_path):
        """
        Test that nested directories (e.g., .github/workflows) are created correctly.
        """
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_directories()
            
            # Check nested path
            nested_path = tmp_path / ".github" / "workflows"
            assert nested_path.exists()
            assert (nested_path / ".gitkeep").exists()
            
        finally:
            os.chdir(original_dir)