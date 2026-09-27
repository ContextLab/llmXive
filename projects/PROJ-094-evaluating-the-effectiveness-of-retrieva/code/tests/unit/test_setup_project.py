import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function we are testing
# Note: Since this file is in code/tests/unit, we need to adjust sys.path
# to import from code/src or code directly if setup_project is at code/
import sys
from pathlib import Path

# Add the parent directory of 'tests' to the path (which is 'code')
# So we can import setup_project
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_project import create_directories

class TestCreateDirectories:
    def test_creates_all_required_dirs(self, tmp_path):
        """
        Verify that create_directories creates all required directories
        defined in task T001a.
        """
        # Change to tmp_path to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the function
            created = create_directories()
            
            # Define expected directories
            expected_dirs = [
                "src/data",
                "src/models",
                "src/analysis",
                "src/cli",
                "src/lib",
                "data/raw",
                "data/processed",
                "results",
                "tests/unit",
                "tests/integration",
                "tests/contract"
            ]
            
            # Verify all expected directories exist
            for expected in expected_dirs:
                assert Path(expected).exists(), f"Directory {expected} was not created"
                assert Path(expected).is_dir(), f"Path {expected} exists but is not a directory"
            
            # Verify the number of created directories matches
            assert len(created) == len(expected_dirs), \
                f"Expected {len(expected_dirs)} directories, got {len(created)}"
            
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_dirs(self, tmp_path):
        """
        Verify that the function doesn't fail if directories already exist.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Pre-create one directory
            Path("src/data").mkdir(parents=True)
            
            # Run the function - should not raise
            created = create_directories()
            
            # Verify it still returns success
            assert "src/data" in created
            
        finally:
            os.chdir(original_cwd)