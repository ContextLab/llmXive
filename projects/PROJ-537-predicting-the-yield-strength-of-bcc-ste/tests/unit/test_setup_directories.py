"""
Unit tests for the directory setup functionality (Task T001).
Verifies that the required project structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the function. Since we are running tests from the repo root,
# we assume the code directory is in the path or we import relative to the script.
# For this test, we will mock the creation in a temp directory to avoid polluting the real repo
# during testing, but we verify the logic.

def test_create_directories_structure():
    """
    Test that create_directories creates all required folders.
    """
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Import the function after changing directory to ensure relative imports work if needed
            # But since setup_directories.py uses pathlib relative to '.', it should work from any CWD
            from setup_directories import create_directories
            
            created = create_directories()
            
            required_paths = [
                "code",
                "data",
                "data/raw",
                "data/intermediate",
                "data/processed",
                "data/provenance",
                "data/results",
                "tests",
                "tests/unit",
                "tests/integration",
                "tests/contract"
            ]
            
            for path_str in required_paths:
                full_path = Path(tmpdir) / path_str
                assert full_path.exists(), f"Directory {path_str} was not created."
                assert full_path.is_dir(), f"Path {path_str} exists but is not a directory."
                
                # Verify it's in the returned list (normalized)
                assert str(full_path) in created, f"Path {full_path} not in returned list."
                
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """
    Test that running the script twice doesn't fail.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            from setup_directories import create_directories
            
            # Run twice
            first_run = create_directories()
            second_run = create_directories()
            
            assert len(first_run) == len(second_run), "Second run created different number of dirs."
            
        finally:
            os.chdir(original_cwd)

def test_non_directory_path_collision():
    """
    Test that the function fails gracefully if a required directory name 
    is taken by a file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create a file named 'code'
            Path("code").touch()
            
            from setup_directories import create_directories
            
            with pytest.raises(RuntimeError, match="not a directory"):
                create_directories()
                
        finally:
            os.chdir(original_cwd)
