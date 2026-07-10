"""
Unit tests for the project setup script (Task T001a).
"""
import os
import shutil
import tempfile
import pytest
import sys

# Add the parent directory to the path to import the setup script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.setup_project import main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_creates_directories(temp_project_root):
    """Test that the setup script creates the required directory structure."""
    # Ensure the directories don't exist before running
    dirs_to_check = [
        "code", "code/utils", "tests", 
        "data/raw", "data/processed", "data/synthetic",
        "models", "docs", "docs/contracts", "state/projects", "logs"
    ]
    
    for d in dirs_to_check:
        if os.path.exists(d):
            shutil.rmtree(d)

    # Run the main function
    exit_code = main()
    
    assert exit_code == 0, "Setup script should return 0 on success"

    # Verify directories were created
    for d in dirs_to_check:
        assert os.path.isdir(d), f"Directory {d} was not created"

def test_handles_existing_directories(temp_project_root):
    """Test that the script handles existing directories gracefully."""
    # Create some directories first
    os.makedirs("code", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)

    # Run the main function
    exit_code = main()
    
    assert exit_code == 0, "Setup script should return 0 even if dirs exist"

def test_fails_on_file_collision(temp_project_root):
    """Test that the script fails if a path exists as a file."""
    # Create a file where a directory should be
    os.makedirs("code", exist_ok=True)
    with open("code/utils", "w") as f:
        f.write("This is a file, not a directory")

    # Run the main function
    exit_code = main()
    
    assert exit_code == 1, "Setup script should return 1 on collision"