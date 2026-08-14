import os
import pytest
from pathlib import Path

# Import the function to test
# Assuming tests are run from project root or we adjust path
import sys
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from code.setup_structure import create_directories

def test_directory_creation(tmp_path):
    """
    Test that create_directories creates the required directory structure.
    We use tmp_path to avoid modifying the real project structure during testing.
    """
    # Change to tmp_path to simulate project root
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    
    try:
        # Call the function
        create_directories()
        
        # Verify directories exist
        required_dirs = [
            "code",
            "code/utils",
            "tests",
            "data/raw",
            "data/processed",
            "data/results",
            "data/results/diagnostics",
            "logs",
            "contracts",
            "figures",
            "specs"
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
