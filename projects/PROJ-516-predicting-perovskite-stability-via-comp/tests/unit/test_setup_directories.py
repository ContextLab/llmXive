"""
Unit tests for the project directory setup script.
Verifies that the expected directories are created or exist.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We import the function from the script we just created.
# Since the script is in 'code/', we need to ensure it's in the path or import relative to project root.
# For this test, we assume the test runner sets the PYTHONPATH to the project root.
try:
    from code.setup_directories import create_directories
except ImportError:
    # Fallback if running directly from tests folder without path setup
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.setup_directories import create_directories

class TestSetupDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that the script creates the required directory structure."""
        original_cwd = os.getcwd()
        try:
            # Change to a temporary directory to simulate a fresh project root
            os.chdir(tmp_path)
            
            # Call the function
            created = create_directories()
            
            # Verify all expected directories exist
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "tests",
                "docs",
                "state"
            ]
            
            for dir_name in expected_dirs:
                assert (tmp_path / dir_name).exists(), f"Directory {dir_name} was not created."
                assert (tmp_path / dir_name).is_dir(), f"{dir_name} is not a directory."
            
            # Verify nested structure for data
            assert (tmp_path / "data/raw").exists()
            assert (tmp_path / "data/processed").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """Test that the script handles existing directories gracefully."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Pre-create one directory
            (tmp_path / "code").mkdir()
            
            # Call the function
            created = create_directories()
            
            # It should not error and should report existing dirs as such
            # The function returns list of newly created dirs
            assert "code" not in created
            assert (tmp_path / "code").exists()
            
        finally:
            os.chdir(original_cwd)