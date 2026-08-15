import os
import shutil
import tempfile
import pytest
from pathlib import Path

# Import the function to test
# Since setup_project is in code/, we need to ensure the import path works
# or adjust sys.path if necessary. However, standard practice is to run
# tests from the root and import code.setup_project.
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.setup_project import main

def test_setup_project_creates_directories(tmp_path):
    """
    Test that setup_project.main() creates the required directory structure.
    We run the script in a temporary directory to avoid polluting the real project.
    """
    # Change to the temporary directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run the setup script
        result = main()
        
        # Check return code
        assert result == 0, "Setup script should return 0 on success"
        
        # Verify directories exist
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts/logs",
            "artifacts/plots",
            "artifacts/reports",
            "contracts",
        ]
        
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_setup_project_handles_existing_directories(tmp_path):
    """
    Test that setup_project.main() handles existing directories gracefully.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Pre-create one of the directories
        pre_created = tmp_path / "code"
        pre_created.mkdir()
        
        # Run the setup script
        result = main()
        
        # Should still succeed
        assert result == 0
        
        # Verify the pre-created directory still exists
        assert pre_created.exists()
        
    finally:
        os.chdir(original_cwd)