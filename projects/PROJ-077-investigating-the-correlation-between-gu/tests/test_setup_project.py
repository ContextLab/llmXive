import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import main
from config import ensure_directories

def test_directories_creation():
    """
    Test that the setup_project.py script creates the required directories
    and returns 0 on success.
    """
    # We assume the script is run from the project root context.
    # Since we can't easily change the working directory in a test
    # without side effects, we verify the logic by checking if the
    # ensure_directories function (called by main) works as expected
    # and if the directories exist after a simulated run.
    
    # Create a temporary directory to simulate the project root
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Run the main function which calls ensure_directories and creates dirs
            result = main()
            
            # Verify exit code
            assert result == 0, "main() should return 0 on success"
            
            # Verify directories exist
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests"
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(tmpdir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} should exist"
                assert dir_path.is_dir(), f"{dir_path} should be a directory"
        finally:
            os.chdir(original_cwd)