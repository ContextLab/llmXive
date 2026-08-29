import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from create_project_dirs import main

class TestCreateProjectDirs:
    """
    Tests for the create_project_dirs script.
    Verifies that the required directory structure is created correctly.
    """

    def test_creates_required_directories(self, tmp_path):
        """
        Test that the script creates all required directories:
        data/raw, data/processed, code, tests, docs
        """
        # Change to the temporary directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the main function
            # We need to capture stdout to avoid cluttering test output, 
            # but the function prints status.
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
            
            # Verify directories exist
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "docs"
            ]
            
            for dir_path_str in required_dirs:
                dir_path = tmp_path / dir_path_str
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"
        
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """
        Test that the script handles existing directories gracefully
        and does not fail if directories already exist.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Pre-create one of the directories
            (tmp_path / "code").mkdir(parents=True)
            
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Should not raise an exception
                main()
            
            # Verify the pre-existing directory is still there
            assert (tmp_path / "code").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_creates_parent_directories(self, tmp_path):
        """
        Test that the script creates parent directories if they don't exist.
        Specifically for 'data/raw' and 'data/processed'.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
            
            # Verify parent 'data' was created
            assert (tmp_path / "data").exists()
            assert (tmp_path / "data").is_dir()
            
            # Verify children
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            
        finally:
            os.chdir(original_cwd)