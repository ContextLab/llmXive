import os
import pytest
from pathlib import Path
import shutil

# Import the function to test
try:
    from setup_dirs import main
except ImportError:
    # Fallback for test runner context where path might need adjustment
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from setup_dirs import main

def test_setup_dirs_creates_structure(tmp_path):
    """
    Test that setup_dirs.main() creates the required directory structure.
    We run it in a temporary directory to avoid polluting the real repo during tests.
    """
    original_cwd = os.getcwd()
    try:
        # Change to the temporary directory
        os.chdir(tmp_path)
        
        # Run the main function
        result = main()
        
        # Verify return code
        assert result == 0, "main() should return 0 on success"
        
        # Verify directories exist
        required_dirs = [
            "data/raw",
            "data/derived",
            "code",
            "tests",
            "results",
            "state"
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)