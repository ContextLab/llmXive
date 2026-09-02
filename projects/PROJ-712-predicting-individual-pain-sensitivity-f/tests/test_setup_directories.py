import os
import shutil
from pathlib import Path
import pytest

# Ensure we can import the code module
sys_path = Path(__file__).parent.parent / "code"
if str(sys_path) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path))

from setup_directories import main

PROJECT_NAME = "PROJ-712-predicting-individual-pain-sensitivity-f"
BASE_PATH = Path("projects") / PROJECT_NAME

@pytest.fixture(autouse=True)
def cleanup_project_dirs():
    """Clean up created directories before and after the test."""
    # Remove if exists
    if BASE_PATH.exists():
        shutil.rmtree(BASE_PATH)
    yield
    # Cleanup after test
    if BASE_PATH.exists():
        shutil.rmtree(BASE_PATH)

def test_directories_created():
    """
    Test that running main() creates the required directory structure.
    This verifies T001a, T001b, and T001c.
    """
    # Run the setup script
    main()
    
    # Define expected paths
    expected_dirs = [
        BASE_PATH / "data" / "raw",
        BASE_PATH / "data" / "processed",
        BASE_PATH / "artifacts",
        BASE_PATH / "state",
        BASE_PATH / "code",
        BASE_PATH / "tests",
    ]
    
    # Assert all directories exist and are directories
    for path in expected_dirs:
        assert path.exists(), f"Directory {path} was not created."
        assert path.is_dir(), f"Path {path} exists but is not a directory."