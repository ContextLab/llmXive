"""
Unit tests for the project structure initialization.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path to import setup_structure
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_structure import main

def test_structure_creation():
    """Test that the script creates all required directories."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Run the main function
            # We need to capture stdout to verify, but main() calls sys.exit(1) on failure
            # We will just run it and catch SystemExit if it fails
            try:
                main()
            except SystemExit as e:
                if e.code != 0:
                    raise AssertionError("setup_structure.main() exited with non-zero code") from e
            
            # Verify directories exist
            required_dirs = [
                "code",
                "tests",
                "data",
                "data/raw",
                "data/processed",
                "data/analysis",
                "artifacts",
                "contracts"
            ]
            
            for dir_name in required_dirs:
                dir_path = Path(temp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created."
                assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory."
                
            print("All assertions passed.")
            
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    test_structure_creation()
    print("Test passed successfully.")