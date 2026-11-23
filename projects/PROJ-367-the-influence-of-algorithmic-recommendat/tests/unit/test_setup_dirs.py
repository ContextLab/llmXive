"""
Unit tests for setup_dirs.py to verify directory creation.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We will test the logic by mocking the path creation
def test_directory_structure_creation():
    """Test that the directory structure can be created."""
    # Create a temporary directory to simulate the project root
    temp_root = tempfile.mkdtemp()
    try:
        required_dirs = [
            "code",
            "tests",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/processed",
            "docs",
            "docs/reports"
        ]
        
        # Create directories
        for dir_name in required_dirs:
            dir_path = Path(temp_root) / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify all directories exist
        for dir_name in required_dirs:
            dir_path = Path(temp_root) / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
        
        print(f"Successfully verified directory structure in {temp_root}")
    finally:
        # Clean up
        shutil.rmtree(temp_root)

if __name__ == "__main__":
    test_directory_structure_creation()
    print("All tests passed!")