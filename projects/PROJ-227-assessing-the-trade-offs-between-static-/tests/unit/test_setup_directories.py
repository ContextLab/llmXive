import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/PROJ-227-assessing-the-trade-offs-between-static-" / "code"))
from setup_directories import main

def test_directory_structure_creation():
    """
    Test that the main function creates the expected directory structure.
    This test runs the creation logic and verifies existence.
    """
    project_root = Path("projects/PROJ-227-assessing-the-trade-offs-between-static-")
    
    # Ensure a clean state for the test by removing the folder if it exists
    # (In a real CI environment, this might be handled by the runner's cleanup)
    if project_root.exists():
        shutil.rmtree(project_root)
    
    # Run the main function
    result = main()
    
    # Assert the function returned success (0)
    assert result == 0, "Directory creation should return 0"
    
    # Verify each required directory exists
    required_dirs = [
        "data/raw",
        "data/processed",
        "state",
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        assert full_path.exists(), f"Directory {full_path} should exist"
        assert full_path.is_dir(), f"{full_path} should be a directory"