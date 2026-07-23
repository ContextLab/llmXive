import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the main function from the sibling module.
# Since the file is in code/setup_directories.py, we add the parent to path if necessary,
# or assume the test runner is configured to find it.
# For this test, we assume the working directory is the project root.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_directories import main

def test_directories_created():
    """
    Test that T001a, T001b, and T001c directories are created by the script.
    """
    # Use a temporary directory to avoid polluting the real project structure during test
    # However, the script uses relative paths. We will run it in a temp dir context.
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run the script
            result = main()
            assert result == 0, "main() should return 0 on success"
            
            project_root = Path("projects/PROJ-712-predicting-individual-pain-sensitivity-f")
            assert project_root.exists(), "Project root directory should exist"
            
            # Verify T001a requirements
            assert (project_root / "data" / "raw").exists(), "data/raw directory missing"
            assert (project_root / "data" / "processed").exists(), "data/processed directory missing"
            
            # Verify T001b requirements (bonus verification)
            assert (project_root / "artifacts").exists(), "artifacts directory missing"
            assert (project_root / "state").exists(), "state directory missing"
            
            # Verify T001c requirements (bonus verification)
            assert (project_root / "code").exists(), "code directory missing"
            assert (project_root / "tests").exists(), "tests directory missing"
            
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """
    Test that running the script twice does not raise errors (idempotent).
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run twice
            main()
            main()
            # If we get here without exception, it passed
            assert True
        finally:
            os.chdir(original_cwd)
