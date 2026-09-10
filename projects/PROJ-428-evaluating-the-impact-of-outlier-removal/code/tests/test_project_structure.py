import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path so we can import src modules
code_path = Path(__file__).parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.setup_dirs import setup_directories

def test_required_directories_exist():
    """
    Test that the setup_directories function creates all required directories.
    """
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a mock 'code' directory structure
        code_dir = temp_path / "code"
        src_dir = code_dir / "src"
        src_dir.mkdir(parents=True)
        
        # Temporarily modify __file__ to point to our mock location
        import src.setup_dirs
        original_file = src.setup_dirs.__file__
        src.setup_dirs.__file__ = str(src_dir / "setup_dirs.py")
        
        try:
            # Run the setup function
            result = setup_directories()
            
            # Verify the result
            assert result["project_root"] == str(temp_path)
            assert result["new_directories_count"] == 4
            
            # Verify each directory exists
            expected_dirs = [
                "data/raw",
                "data/processed",
                "data/results",
                "state"
            ]
            
            for dir_path in expected_dirs:
                full_path = temp_path / dir_path
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"Path {full_path} is not a directory"
        finally:
            # Restore original __file__
            src.setup_dirs.__file__ = original_file

def test_project_root_is_writable():
    """
    Test that the project root is writable by attempting to create a file.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a mock 'code' directory structure
        code_dir = temp_path / "code"
        src_dir = code_dir / "src"
        src_dir.mkdir(parents=True)
        
        # Temporarily modify __file__ to point to our mock location
        import src.setup_dirs
        original_file = src.setup_dirs.__file__
        src.setup_dirs.__file__ = str(src_dir / "setup_dirs.py")
        
        try:
            # Run setup to create directories
            setup_directories()
            
            # Try to create a test file in one of the directories
            test_file = temp_path / "data" / "raw" / "test_writable.txt"
            test_file.write_text("Test content")
            
            assert test_file.exists(), "Could not write to data/raw directory"
            assert test_file.read_text() == "Test content"
        finally:
            # Restore original __file__
            src.setup_dirs.__file__ = original_file
            # Clean up test file
            if 'test_file' in locals():
                test_file.unlink()