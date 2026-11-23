import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the script
# This assumes tests are run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.setup_project_structure import create_directories

def test_directory_creation(tmp_path):
    """Test that the directory creation function creates the required structure."""
    # Change to the temp directory to avoid polluting the actual project
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run the creation function
        create_directories()
        
        # Verify expected directories exist
        expected_dirs = [
            "code/simulation",
            "code/models",
            "code/metrics",
            "code/validation",
            "code/plots",
            "code/scripts",
            "data/raw",
            "data/simulated",
            "data/results",
            "tests/unit",
            "tests/integration",
            "docs/paper"
        ]
        
        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
        
        # Verify .gitkeep files exist in data directories
        gitkeep_dirs = ["data/raw", "data/simulated", "data/results", "docs/paper"]
        for dir_path in gitkeep_dirs:
            full_path = tmp_path / dir_path / ".gitkeep"
            assert full_path.exists(), f".gitkeep file missing in {dir_path}"
            assert full_path.is_file(), f".gitkeep in {dir_path} is not a file"
            
    finally:
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """Test that running the creation function twice doesn't cause errors."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run twice
        create_directories()
        create_directories()
        
        # Verify structure still exists
        assert (tmp_path / "code/simulation").exists()
        assert (tmp_path / "data/raw").exists()
        
    finally:
        os.chdir(original_cwd)