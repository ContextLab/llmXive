import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from setup_project_structure import setup_directories

class TestSetupProjectStructure:
    def test_creates_directories(self, tmp_path):
        """Test that setup_directories creates the required folder structure."""
        # Change to temporary directory to avoid polluting real project
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup function
            result = setup_directories()
            
            assert result is True
            
            # Verify expected directories exist
            expected_dirs = [
                "src",
                "tests",
                "data/raw",
                "data/processed",
                "data/splits",
                "results",
                "contracts",
                ".github/workflows"
            ]
            
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
                # Check for .gitkeep
                gitkeep = dir_path / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep missing in {dir_name}"
                
        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        """Test that running setup_directories twice does not cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run twice
            setup_directories()
            setup_directories()
            
            # Verify structure still exists and is valid
            assert (tmp_path / "src").exists()
            assert (tmp_path / "data/raw").exists()
            
        finally:
            os.chdir(original_cwd)