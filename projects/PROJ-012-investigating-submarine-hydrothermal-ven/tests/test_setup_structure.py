"""
Test to verify that the project structure setup script runs correctly
and creates the required directories and files.
"""
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
import sys

def test_project_structure_creation():
    """
    Verify that setup_structure.py creates the required directories.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        os.chdir(project_root)
        
        # Run the setup script
        result = subprocess.run(
            [sys.executable, "code/setup_structure.py"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Verify the script ran successfully
        assert result.returncode == 0, f"Setup script failed: {result.stderr}"
        
        # Define expected directories
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "state",
            "results/figures",
            "specs",
            "contracts",
            "docs"
        ]
        
        # Check that all directories exist
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory missing: {dir_name}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_name}"
        
        # Check that placeholder files exist
        expected_files = [
            "data/raw/.gitkeep",
            "data/processed/.gitkeep",
            "code/.gitkeep",
            "tests/.gitkeep",
            "state/.gitkeep",
            "results/figures/.gitkeep",
            "specs/README.md",
            "contracts/README.md",
            "docs/README.md"
        ]
        
        for file_name in expected_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"Placeholder file missing: {file_name}"
            assert file_path.is_file(), f"Path is not a file: {file_name}"
        
        print("All project structure checks passed.")

if __name__ == "__main__":
    test_project_structure_creation()
    print("Test completed successfully.")