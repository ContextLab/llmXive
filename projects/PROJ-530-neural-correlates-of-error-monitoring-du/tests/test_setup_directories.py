import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from setup_directories import create_project_directories

def test_create_project_directories():
    """
    Test that create_project_directories creates all required subdirectories.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Call the function
        create_project_directories(str(project_root))
        
        # Define expected directories
        expected_dirs = [
            "results/models",
            "results/figures",
            "results/diagnostics",
            "code",
            "tests"
        ]
        
        # Verify each directory exists
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_create_project_directories_idempotent():
    """
    Test that running the function twice does not raise errors (idempotent).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Run twice
        create_project_directories(str(project_root))
        create_project_directories(str(project_root))
        
        # Verify directories still exist
        assert (project_root / "code").exists()
        assert (project_root / "tests").exists()
        assert (project_root / "results/models").exists()
