import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import setup_directories
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_directories import create_directories

def test_create_directories_structure(tmp_path):
    """Test that create_directories creates all required directories."""
    # Change to tmp_path to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Create a fake code directory to trigger the logic
        (tmp_path / "code").mkdir()
        
        # Run the function
        result = create_directories()
        
        # Verify result
        assert result is True, "create_directories should return True on success"
        
        # Verify all required directories exist
        required_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/processed",
            "data/simulations",
            "data/reports",
            "docs"
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
        
        # Verify nested structure
        assert (tmp_path / "data" / "raw").exists(), "data/raw should exist"
        assert (tmp_path / "data" / "processed").exists(), "data/processed should exist"
        assert (tmp_path / "data" / "simulations").exists(), "data/simulations should exist"
        assert (tmp_path / "data" / "reports").exists(), "data/reports should exist"
        
    finally:
        os.chdir(original_cwd)

def test_create_directories_idempotent(tmp_path):
    """Test that create_directories can be run multiple times without error."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Create a fake code directory
        (tmp_path / "code").mkdir()
        
        # Run twice
        result1 = create_directories()
        result2 = create_directories()
        
        assert result1 is True
        assert result2 is True
        
    finally:
        os.chdir(original_cwd)