import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root(tmp_path):
    """Create a temporary project root for testing structure creation."""
    return tmp_path

def test_required_directories_exist(project_root):
    """
    Test that the required project structure directories exist after creation.
    
    This test verifies that T001 (Create project structure) has been implemented
    correctly by checking for the existence of:
    - code/
    - data/raw/
    - data/interim/
    - data/processed/
    - tests/
    """
    # Define the required directories relative to project root
    required_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests",
        "reports",
        "docs"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory '{dir_name}' should exist"
        assert dir_path.is_dir(), f"'{dir_name}' should be a directory"

def test_data_subdirectories_structure(project_root):
    """
    Test that data subdirectories are properly nested.
    """
    data_dirs = ["raw", "interim", "processed"]
    
    for subdir in data_dirs:
        dir_path = project_root / "data" / subdir
        assert dir_path.exists(), f"Directory 'data/{subdir}' should exist"

def test_create_structure_script_executes(project_root, monkeypatch):
    """
    Test that the create_structure.py script can be executed and creates directories.
    """
    # Change to the temporary project root
    monkeypatch.chdir(project_root)
    
    # Import and run the main function from create_structure
    import sys
    sys.path.insert(0, str(project_root))
    
    # We need to simulate the script being run from the 'code' directory context
    # but the directories should be created relative to the project root
    from create_structure import main
    
    # Run the script
    exit_code = main()
    
    # Verify the script exited successfully
    assert exit_code == 0, "create_structure.py should exit with code 0"
    
    # Verify directories were created
    required_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests",
        "reports",
        "docs"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory '{dir_name}' should exist after script execution"
