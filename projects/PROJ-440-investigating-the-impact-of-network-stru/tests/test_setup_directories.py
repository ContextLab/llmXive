import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to ensure the module can be imported
# Since we are running tests from the root, we might need to adjust sys.path
# or rely on the test runner configuration.
# Assuming standard pytest behavior where code/ is in the path or we import relative to root.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_directories import setup_directories

def test_setup_directories_creates_all_required_dirs():
    """
    Test that setup_directories creates all required directories.
    """
    # Create a temporary directory to simulate the project root
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run the setup function
            result = setup_directories()
            
            # Verify the function returned True
            assert result is True
            
            # Define the expected directories
            expected_dirs = [
                "code",
                "data",
                "data/raw",
                "data/processed",
                "data/analysis",
                "tests",
                "contracts",
                "state"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = Path(dir_name)
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"
            
            # Verify nested structure
            assert (Path("data/raw")).exists()
            assert (Path("data/processed")).exists()
            assert (Path("data/analysis")).exists()
            
        finally:
            os.chdir(original_cwd)

def test_setup_directories_idempotent():
    """
    Test that running setup_directories multiple times does not cause errors.
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run twice
            setup_directories()
            result2 = setup_directories()
            
            # Both should succeed
            assert result2 is True
            
            # Verify directories still exist
            assert Path("code").exists()
            assert Path("data/raw").exists()
            
        finally:
            os.chdir(original_cwd)
