import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path to allow imports
# Assuming tests are run from the project root
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project_structure import create_directories

class TestSetupProjectStructure:
    """Tests for the project structure creation logic."""

    def test_creates_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to temp directory to isolate test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Call the function
            create_directories()
            
            # Define expected directories
            expected_dirs = [
                "code",
                "code/utils",
                "data/raw",
                "data/processed",
                "tests/unit",
                "tests/integration",
                "docs/figures",
                "state"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories are not overwritten or cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Pre-create some directories
            (tmp_path / "code").mkdir()
            (tmp_path / "data").mkdir()
            (tmp_path / "data" / "raw").mkdir()
            
            # Call the function - should not raise
            result = create_directories()
            assert result is True
            
            # Verify pre-existing directories still exist
            assert (tmp_path / "code").exists()
            assert (tmp_path / "data" / "raw").exists()
        finally:
            os.chdir(original_cwd)

    def test_creates_nested_directories(self, tmp_path):
        """Verify that nested directories (e.g., code/utils) are created correctly."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_directories()
            
            # Check nested paths
            assert (tmp_path / "code" / "utils").exists()
            assert (tmp_path / "tests" / "unit").exists()
            assert (tmp_path / "tests" / "integration").exists()
            assert (tmp_path / "docs" / "figures").exists()
        finally:
            os.chdir(original_cwd)