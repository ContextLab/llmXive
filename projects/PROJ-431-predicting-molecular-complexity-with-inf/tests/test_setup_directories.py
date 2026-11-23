"""
Tests for the setup_directories module.
Verifies that the correct directory structure is created.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_directories
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_directories_created(temp_project_root, capsys):
    """Test that all required directories are created."""
    # Change to the temp directory to simulate running the script in a project root
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        # Run the main function
        exit_code = main()
        
        # Assert exit code is 0
        assert exit_code == 0
        
        # Define expected directories
        expected_dirs = [
            "data/raw",
            "data/processed",
            "results/models",
            "results/reports",
            "results/plots",
            "code",
            "tests"
        ]
        
        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = temp_project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
        
        # Capture output to verify logging
        captured = capsys.readouterr()
        assert "Created" in captured.out or "CREATED" in captured.out
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_directories_exist_already(temp_project_root, capsys):
    """Test that existing directories are skipped."""
    # Pre-create one of the directories
    (temp_project_root / "code").mkdir()
    
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        exit_code = main()
        assert exit_code == 0
        
        captured = capsys.readouterr()
        assert "SKIP" in captured.out or "skip" in captured.out.lower()
        
    finally:
        os.chdir(original_cwd)
