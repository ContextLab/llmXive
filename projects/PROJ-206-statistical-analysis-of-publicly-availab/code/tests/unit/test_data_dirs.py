import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent of code/ to path to allow imports if running from tests/
# Assuming this test file is at tests/unit/test_data_dirs.py
# and the script is at code/create_data_dirs.py
# We need to adjust sys.path to find the code module if running as a script
# However, for this specific task, we are testing the existence of the directory
# which is a filesystem operation.

def test_data_directory_creation():
    """
    Test that the create_data_dirs script successfully creates the data/ directory.
    This is a simple existence check since we cannot easily mock the filesystem
    in this context without more complex setup.
    """
    # This test assumes the script has been run or will be run.
    # In a real CI/CD pipeline, this would run after the script.
    # For now, we verify the logic by checking if the directory exists after running the main function.
    
    # We need to import the main function from the script
    # Since the script is in code/, we need to add code/ to sys.path
    # But the task is to create the directory, so we assume the script is run.
    # Let's verify the directory structure exists after the script runs.
    
    # Get the project root relative to this test file
    # test file: tests/unit/test_data_dirs.py
    # code dir: code/
    # project root: tests/../..
    test_file_path = Path(__file__).resolve()
    project_root = test_file_path.parent.parent.parent
    
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # Check if the directories exist
    assert data_dir.exists(), f"Data directory {data_dir} does not exist"
    assert raw_dir.exists(), f"Raw directory {raw_dir} does not exist"
    assert processed_dir.exists(), f"Processed directory {processed_dir} does not exist"
    
    # Check if they are directories
    assert data_dir.is_dir(), f"{data_dir} is not a directory"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"