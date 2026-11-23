import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the function to test
import sys
# Ensure the code directory is in the path if running from tests root
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project_structure import setup_directories

def test_setup_directories_creates_structure():
    """
    Verify that setup_directories creates the required folders:
    data/raw, data/processed, code, tests, results
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Mock the current working directory to be inside the temp dir
        # We need to patch the function or run it in a way that it uses tmp_path
        # Since the function uses Path.cwd(), we change cwd temporarily
        original_cwd = Path.cwd()
        
        try:
            os.chdir(tmp_path)
            
            # Run the setup
            # The function looks for "PROJ-118..." or uses cwd.
            # Since we are in a temp dir with that name, we rename it
            new_name = "PROJ-118-investigating-the-neural-correlates-of-p"
            new_path = tmp_path / new_name
            new_path.mkdir()
            os.chdir(new_path)
            
            result_root = setup_directories()
            
            # Verify the root is what we expect
            assert result_root == new_path
            
            # Verify directories exist
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "results"
            ]
            
            for dir_name in required_dirs:
                dir_path = result_root / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created."
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory."
                
            # Verify .gitkeep exists in data directories
            for data_dir in ["data/raw", "data/processed"]:
                gitkeep_path = result_root / data_dir / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep missing in {data_dir}"
                
        finally:
            os.chdir(original_cwd)

def test_setup_directories_idempotent():
    """
    Verify that running setup_directories twice does not fail.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        new_name = "PROJ-118-investigating-the-neural-correlates-of-p"
        new_path = tmp_path / new_name
        new_path.mkdir()
        
        original_cwd = Path.cwd()
        try:
            os.chdir(new_path)
            
            # Run twice
            setup_directories()
            setup_directories()
            
            # Should not raise an exception
            assert True
            
        finally:
            os.chdir(original_cwd)
