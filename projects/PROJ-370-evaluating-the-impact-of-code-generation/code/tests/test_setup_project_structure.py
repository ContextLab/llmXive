import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the function to test
# Note: The API surface says 'from code.setup_project_structure import create_directories'
# but since we are in code/tests, we need to adjust the import path or sys.path.
# Assuming the project root is the parent of 'code' or we run from project root.
# To be safe, we add the parent of 'tests' to sys.path if not already there.
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent # This is 'code'
# We need to import from 'setup_project_structure' which is in 'code'
# The API surface says: import as `from setup_project_structure import create_directories`
# Wait, the API surface says: `import as: from code/setup_project_structure.py` -> `from code.setup_project_structure import create_directories`?
# Actually the API surface says: `import as: from setup_project_structure import create_directories` but the file is `code/setup_project_structure.py`.
# Let's assume standard python path usage where 'code' is not a package but the script is run from root.
# However, the task asks to implement T001. The file `setup_project_structure.py` is created in `code/`.
# Let's add the parent of 'code' to path if running from tests, or just import relative to current file structure.

# Let's assume the script is executed from the project root (where 'code' is a subdirectory).
# The import in the task description might be slightly ambiguous, but standard practice is:
# If running `python code/setup_project_structure.py`, it works.
# If running from `code/tests`, we need to ensure `code` is in path.

sys.path.insert(0, str(current_dir.parent)) 

from setup_project_structure import create_directories

class TestSetupProjectStructure:
    
    def test_create_directories_creates_all_required(self, tmp_path):
        """
        Test that create_directories creates all required subdirectories.
        We patch the working directory to a temporary directory.
        """
        required_dirs = [
            "src",
            "data/raw",
            "data/derived",
            "data/annotations",
            "results",
            "tests",
            "specs"
        ]
        
        # Change to tmp_path for the test
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the function
            result = create_directories()
            
            assert result is True
            
            # Verify directories exist
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
        finally:
            os.chdir(original_cwd)
    
    def test_create_directories_skips_existing(self, tmp_path):
        """
        Test that create_directories handles existing directories gracefully.
        """
        # Pre-create one directory
        existing_dir = tmp_path / "src"
        existing_dir.mkdir(parents=True, exist_ok=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            result = create_directories()
            
            assert result is True
            assert existing_dir.exists()
            
        finally:
            os.chdir(original_cwd)
    
    def test_nested_data_directories_created(self, tmp_path):
        """
        Specifically verify that nested paths like data/raw are created correctly.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            create_directories()
            
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "derived").exists()
            assert (tmp_path / "data" / "annotations").exists()
            
        finally:
            os.chdir(original_cwd)