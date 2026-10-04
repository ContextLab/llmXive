import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path if running tests directly
# This allows importing from code/ if needed, though T002 mostly tests os.makedirs
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_project_structure import create_directories, verify_directories, main

class TestProjectStructure:
    """
    Tests for T002: Create project structure.
    Verifies that code/, tests/, and data/ directories are created and exist.
    """

    def test_create_directories(self, tmp_path):
        """
        Test that create_directories creates the required folders.
        We use tmp_path to isolate the test environment.
        """
        # Change to tmp_path to simulate the project root
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Mock the get_project_root behavior if necessary, 
            # but create_directories uses Path.cwd() directly.
            create_directories()
            
            # Verify directories exist
            assert (tmp_path / 'code').is_dir(), "code/ directory not created"
            assert (tmp_path / 'tests').is_dir(), "tests/ directory not created"
            assert (tmp_path / 'data').is_dir(), "data/ directory not created"
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_success(self, tmp_path):
        """
        Test that verify_directories passes when directories exist.
        """
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create the directories first
            os.makedirs(str(tmp_path / 'code'), exist_ok=True)
            os.makedirs(str(tmp_path / 'tests'), exist_ok=True)
            os.makedirs(str(tmp_path / 'data'), exist_ok=True)
            
            # This should not raise an exception
            verify_directories()
        finally:
            os.chdir(original_cwd)

    def test_verify_directories_failure(self, tmp_path):
        """
        Test that verify_directories fails when a directory is missing.
        """
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Create only 'code'
            os.makedirs(str(tmp_path / 'code'), exist_ok=True)
            # 'tests' and 'data' are missing
            
            with pytest.raises(FileNotFoundError):
                verify_directories()
        finally:
            os.chdir(original_cwd)

    def test_main_function(self, tmp_path):
        """
        Test the main function entry point.
        """
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # This should run without error and create directories
            # We can't easily capture stdout in pytest without capsys, 
            # but we can check for side effects.
            main()
            
            assert (tmp_path / 'code').is_dir()
            assert (tmp_path / 'tests').is_dir()
            assert (tmp_path / 'data').is_dir()
        finally:
            os.chdir(original_cwd)
