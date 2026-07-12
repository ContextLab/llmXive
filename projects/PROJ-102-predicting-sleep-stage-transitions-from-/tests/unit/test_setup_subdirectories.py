import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_subdirectories import main

def test_creates_required_subdirectories():
    """
    Test that the script creates src/data, src/features, src/models, src/utils.
    """
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the main function
            exit_code = main()
            
            # Verify exit code
            assert exit_code == 0, "Script should exit with code 0"
            
            # Verify directories were created
            required_dirs = [
                "src/data",
                "src/features",
                "src/models",
                "src/utils"
            ]
            
            for dir_name in required_dirs:
                full_path = Path(tmp_dir) / dir_name
                assert full_path.exists(), f"Directory {dir_name} should exist"
                assert full_path.is_dir(), f"{dir_name} should be a directory"
        
        finally:
            os.chdir(original_cwd)

def test_handles_existing_directories():
    """
    Test that the script handles the case where directories already exist.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Pre-create the directories
            (Path(tmp_dir) / "src").mkdir(parents=True)
            (Path(tmp_dir) / "src" / "data").mkdir()
            (Path(tmp_dir) / "src" / "features").mkdir()
            (Path(tmp_dir) / "src" / "models").mkdir()
            (Path(tmp_dir) / "src" / "utils").mkdir()
            
            # Run the main function
            exit_code = main()
            
            # Verify exit code
            assert exit_code == 0, "Script should exit with code 0"
            
            # Verify directories still exist and are valid
            required_dirs = [
                "src/data",
                "src/features",
                "src/models",
                "src/utils"
            ]
            
            for dir_name in required_dirs:
                full_path = Path(tmp_dir) / dir_name
                assert full_path.exists(), f"Directory {dir_name} should still exist"
        
        finally:
            os.chdir(original_cwd)