import os
import tempfile
import shutil
import pytest
import sys

# Add the parent directory to the path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.setup_gitkeep import initialize_gitkeeps

def test_gitkeep_creation(tmp_path):
    """
    Test that initialize_gitkeeps creates .gitkeep files in specified directories.
    """
    # Create a temporary directory structure to simulate the project
    # We will temporarily change the working directory to test
    original_cwd = os.getcwd()
    
    try:
        # Create temp project root
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        os.chdir(test_root)

        # Create the required directory structure
        dirs = [
            "code", "data", "data/raw", "data/processed", "data/visualizations",
            "tests", "tests/unit", "tests/integration", "docs"
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

        # Run the function
        count = initialize_gitkeeps()

        # Verify files were created
        assert count == len(dirs), f"Expected {len(dirs)} files, got {count}"

        for d in dirs:
            gitkeep_path = os.path.join(d, ".gitkeep")
            assert os.path.exists(gitkeep_path), f".gitkeep missing in {d}"
            assert os.path.isfile(gitkeep_path), f".gitkeep in {d} is not a file"

    finally:
        os.chdir(original_cwd)

def test_skips_existing_gitkeep(tmp_path):
    """
    Test that initialize_gitkeeps does not overwrite existing .gitkeep files.
    """
    original_cwd = os.getcwd()
    try:
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        os.chdir(test_root)

        # Create a directory with an existing .gitkeep
        os.makedirs("code", exist_ok=True)
        existing_path = os.path.join("code", ".gitkeep")
        with open(existing_path, "w") as f:
            f.write("existing content")

        # Run the function
        count = initialize_gitkeeps()

        # Verify it wasn't overwritten and count is correct (only creates for missing)
        # Note: The function counts creation. Since 'code' already has one, it shouldn't count it.
        # But the loop iterates 9 times. Let's check the specific logic in the function.
        # The function returns count of CREATED files.
        
        with open(existing_path, "r") as f:
            content = f.read()
        assert content == "existing content", "Existing .gitkeep was overwritten"
        
        # The function should return 8 (since code/ already had one)
        # But wait, the function logic: if not exists -> create -> count += 1
        # So if 'code' exists, it doesn't increment.
        # We created 8 other dirs without .gitkeep.
        assert count == 8, f"Expected 8 new files, got {count}"

    finally:
        os.chdir(original_cwd)