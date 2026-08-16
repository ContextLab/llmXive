import os
import pytest
from pathlib import Path
import shutil

# Import the function to test
# We need to ensure the code directory is in the path if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_dirs import main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to act as the project root."""
    return tmp_path

def test_setup_dirs_creates_structure(temp_project_root, monkeypatch):
    """Test that setup_dirs creates the required directory structure."""
    # Change CWD to the temporary directory to simulate running from project root
    monkeypatch.chdir(temp_project_root)
    
    project_name = "PROJ-150-detecting-statistical-power-drift-in-rep"
    expected_project_path = temp_project_root / project_name
    
    # Run the main function
    result = main()
    
    # Assert return code is 0
    assert result == 0
    
    # Assert main project directory exists
    assert expected_project_path.exists()
    assert expected_project_path.is_dir()
    
    # Assert all required subdirectories exist
    required_subdirs = [
        "data/raw",
        "data/derived",
        "code",
        "tests",
        "results",
        "state"
    ]
    
    for subdir in required_subdirs:
        full_path = expected_project_path / subdir
        assert full_path.exists(), f"Missing directory: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"
