import os
import sys
import pytest
from pathlib import Path

# Add the parent directory to the path to import from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project import create_directories

class TestCreateDirectories:
    def test_creates_required_structure(self, tmp_path):
        """
        Test that create_directories creates the required folder structure
        within a temporary directory.
        """
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the function
            result = create_directories()
            
            assert result is True
            
            # Verify directories exist
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "reports",
                "reports/figures",
                "tests/unit",
                "tests/contract"
            ]
            
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """
        Test that the function handles pre-existing directories gracefully.
        """
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create one directory manually first
            (tmp_path / "code").mkdir()
            
            # Run the function
            result = create_directories()
            
            assert result is True
            assert (tmp_path / "code").exists()
            
        finally:
            os.chdir(original_cwd)