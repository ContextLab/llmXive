import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from code.setup_project_structure import setup_directories

class TestSetupProjectStructure:
    """Tests for the setup_project_structure.py script."""

    def test_setup_directories_creates_all_required_dirs(self, tmp_path):
        """Verify that setup_directories creates all required directories."""
        # Change to the temporary directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup function
            result = setup_directories()
            
            # Assert the function returned True (success)
            assert result is True
            
            # Verify all required directories exist
            required_dirs = [
                "src",
                "tests",
                "data/raw",
                "data/processed",
                "data/splits",
                "results",
                "contracts",
                ".github/workflows"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_setup_directories_handles_existing_dirs(self, tmp_path):
        """Verify that setup_directories handles pre-existing directories gracefully."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            # Pre-create some directories
            (tmp_path / "src").mkdir()
            (tmp_path / "results").mkdir()
            
            # Run the setup function
            result = setup_directories()
            
            # Should still succeed
            assert result is True
            
            # Verify all directories still exist
            required_dirs = [
                "src", "tests", "data/raw", "data/processed",
                "data/splits", "results", "contracts", ".github/workflows"
            ]
            
            for dir_name in required_dirs:
                assert (tmp_path / dir_name).exists()
        finally:
            os.chdir(original_cwd)

    def test_setup_directories_creates_nested_dirs(self, tmp_path):
        """Verify that nested directories (like .github/workflows) are created correctly."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            result = setup_directories()
            assert result is True
            
            # Specifically check nested directory
            github_workflows = tmp_path / ".github" / "workflows"
            assert github_workflows.exists()
            assert github_workflows.is_dir()
        finally:
            os.chdir(original_cwd)