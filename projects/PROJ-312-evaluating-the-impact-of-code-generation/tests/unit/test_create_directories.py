import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent to path to allow imports if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects" / "PROJ-312-evaluating-the-impact-of-code-generation" / "code"))

from create_directories import main

def test_directory_structure_created(tmp_path):
    """
    Test that the main function creates the expected directory structure.
    We run the script in a temporary directory to verify file system changes.
    """
    # Save original cwd
    original_cwd = os.getcwd()
    
    try:
        # Change to temp directory to simulate project root
        os.chdir(tmp_path)
        
        # Create a dummy projects folder structure to match the script's expectation
        # The script expects to run from the repo root and create projects/PROJ-312...
        # We need to ensure the script runs successfully in the temp env.
        
        # Execute the main function
        result = main()
        
        # Verify result code
        assert result == 0, "Main function should return 0 on success"
        
        # Verify base directory exists
        base_dir = tmp_path / "projects" / "PROJ-312-evaluating-the-impact-of-code-generation"
        assert base_dir.exists(), f"Base directory {base_dir} should exist"
        
        # Verify subdirectories
        required_dirs = [
            "code", "data", "tests", "contracts", "artifacts", "state",
            "data/raw", "data/processed", "data/spot_check",
            "tests/unit", "tests/contract", "tests/integration"
        ]
        
        for subdir in required_dirs:
            full_path = base_dir / subdir
            assert full_path.exists(), f"Directory {full_path} should exist"
            assert full_path.is_dir(), f"{full_path} should be a directory"
            
    finally:
        # Restore original cwd
        os.chdir(original_cwd)