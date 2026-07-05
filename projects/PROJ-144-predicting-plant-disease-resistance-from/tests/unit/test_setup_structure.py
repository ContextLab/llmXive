"""
Unit tests for the project structure setup script.
Verifies that the required directories are created.
"""
import os
import tempfile
import shutil
import pytest

# Import the function to test
# We need to temporarily add the code directory to the path if running from tests
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_project_structure import create_structure

class TestProjectStructure:
    def test_creates_required_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_structure(tmpdir)
            
            required_dirs = [
                "code",
                "code/utils",
                "code/data",
                "code/modeling",
                "data/raw",
                "data/processed",
                "data/figures",
                "tests/unit",
                "tests/integration",
                "state",
                "results",
                "specs",
            ]
            
            for dir_name in required_dirs:
                full_path = os.path.join(tmpdir, dir_name)
                assert os.path.exists(full_path), f"Directory {dir_name} was not created."
                assert os.path.isdir(full_path), f"Path {dir_name} is not a directory."

    def test_idempotent_creation(self):
        """Test that running the script twice does not cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First run
            create_structure(tmpdir)
            
            # Second run
            try:
                create_structure(tmpdir)
            except Exception as e:
                pytest.fail(f"Idempotent run failed: {e}")