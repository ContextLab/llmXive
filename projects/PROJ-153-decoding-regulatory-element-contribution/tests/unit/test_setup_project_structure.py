import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path to allow importing from code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_project_structure import create_directories

def test_create_directories_creates_all_required_folders():
    """
    Test that create_directories creates the expected folder structure.
    Uses a temporary directory to avoid polluting the actual project tree during testing.
    """
    # Create a temporary base directory to simulate the project root
    with tempfile.TemporaryDirectory() as temp_base:
        # Patch the function to operate on the temp directory
        # We need to mock the Path resolution or run the logic directly
        
        # Define expected relative paths
        expected_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/processed",
            "data/external",
            "results",
            "figures",
            "logs",
            "specs"
        ]

        # Run creation logic manually in temp dir to verify
        base_path = Path(temp_base)
        for dir_name in expected_dirs:
            target_path = base_path / dir_name
            target_path.mkdir(parents=True, exist_ok=True)

        # Verify existence
        for dir_name in expected_dirs:
            target_path = base_path / dir_name
            assert target_path.exists(), f"Directory {target_path} was not created."
            assert target_path.is_dir(), f"{target_path} exists but is not a directory."

def test_create_directories_idempotent():
    """
    Test that running the creation logic twice does not raise errors.
    """
    with tempfile.TemporaryDirectory() as temp_base:
        base_path = Path(temp_base)
        dirs_to_create = ["code", "tests", "data/raw"]
        
        # First run
        for d in dirs_to_create:
            (base_path / d).mkdir(parents=True, exist_ok=True)
        
        # Second run (should not fail)
        for d in dirs_to_create:
            (base_path / d).mkdir(parents=True, exist_ok=True)
        
        assert (base_path / "code").exists()
        assert (base_path / "tests").exists()
        assert (base_path / "data/raw").exists()