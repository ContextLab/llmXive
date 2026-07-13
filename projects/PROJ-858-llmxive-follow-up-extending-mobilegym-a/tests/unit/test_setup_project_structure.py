import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_directories

def test_directory_creation(tmp_path):
    """Test that all required directories are created."""
    # Change to a temporary directory to simulate a project root
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        
        # Run the directory creation
        result = create_directories()
        
        assert result is True, "create_directories should return True on success"
        
        # Verify all required directories exist
        required_dirs = [
            "code",
            "code/scheduler",
            "code/training",
            "code/analysis",
            "code/utils",
            "data/raw",
            "data/processed",
            "data/validation",
            "tests/unit",
            "tests/integration",
            "contracts",
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_idempotent_creation(tmp_path):
    """Test that running the script twice doesn't cause errors."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        
        # Run twice
        create_directories()
        result_second = create_directories()
        
        assert result_second is True, "Second run should also succeed"
        
        # Verify directories still exist
        required_dirs = ["code", "data/raw", "tests/unit", "contracts"]
        for dir_name in required_dirs:
            assert (tmp_path / dir_name).exists()
            
    finally:
        os.chdir(original_cwd)