import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_directories
# Assuming the test is run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories

def test_create_directories_structure():
    """
    Test that create_directories creates the required folder structure.
    """
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run the function
            result = create_directories()
            
            # Verify return value
            assert result is True, "create_directories should return True"
            
            # Verify directories exist
            base_path = Path(tmpdir)
            
            required_dirs = [
                base_path / "code",
                base_path / "data" / "raw",
                base_path / "data" / "processed",
                base_path / "data" / "features",
                base_path / "tests",
                base_path / "state" / "projects",
                base_path / "tests" / "contract",
                base_path / "tests" / "integration",
                base_path / "tests" / "unit",
            ]
            
            for directory in required_dirs:
                assert directory.exists(), f"Directory {directory} should exist"
                assert directory.is_dir(), f"{directory} should be a directory"
            
            print("All required directories created successfully.")
            
        finally:
            os.chdir(original_cwd)

def test_create_directories_idempotent():
    """
    Test that running create_directories multiple times doesn't fail.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Run twice
            create_directories()
            create_directories()
            
            # Should not raise any exceptions
            assert True, "Running create_directories multiple times should not fail"
            
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    test_create_directories_structure()
    test_create_directories_idempotent()
    print("All tests passed.")
