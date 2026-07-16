import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
# Assuming this test runs from the project root or tests/ directory
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import create_directories

def test_create_directories_creates_structure():
    """
    Test that create_directories creates all required directories.
    """
    # Create a temporary directory to act as the project root for this test
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Call the function
            result = create_directories()
            
            # Verify the returned dictionary contains the expected keys
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/reports",
                "tests",
                "state"
            ]
            
            for dir_name in expected_dirs:
                assert dir_name in result, f"Missing directory {dir_name} in result"
                
                # Verify the path exists on disk
                full_path = Path(tmp_dir) / dir_name
                assert full_path.exists(), f"Directory {full_path} does not exist on disk"
                assert full_path.is_dir(), f"Path {full_path} is not a directory"
                
        finally:
            os.chdir(original_cwd)

def test_create_directories_idempotent():
    """
    Test that calling create_directories multiple times does not raise errors.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Call once
            result1 = create_directories()
            
            # Call again
            result2 = create_directories()
            
            # Both should succeed and return the same structure
            assert len(result1) == len(result2)
            
        finally:
            os.chdir(original_cwd)

def test_create_directories_nested_structure():
    """
    Test that nested directories (like data/raw) are created correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            result = create_directories()
            
            # Check specific nested paths
            raw_path = Path(tmp_dir) / "data" / "raw"
            processed_path = Path(tmp_dir) / "data" / "processed"
            
            assert raw_path.exists() and raw_path.is_dir()
            assert processed_path.exists() and processed_path.is_dir()
            
        finally:
            os.chdir(original_cwd)
