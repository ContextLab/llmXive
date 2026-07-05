import os
import pytest
from pathlib import Path
import shutil

# Import the function to test
# Since the file is in code/utils/, we need to adjust sys.path or import relative to root
# Assuming tests are run from the project root (where this file is located relative to code/)
# We will add the parent directory to path to import utils.setup_directories
import sys
from pathlib import Path

# Add the project root to the path if not already present
# We assume the test is run from the root, and code/ is a sibling to tests/
current_dir = Path(__file__).parent
# If tests/ is at root, then code/ is at current_dir.parent / "code"
# But based on the artifact path structure in the prompt, the project root seems to be
# the directory containing 'code', 'tests', 'data', etc.
# Let's dynamically find the project root by looking for 'code' and 'tests'

def get_project_root():
    # Start from current test file
    curr = Path(__file__).resolve()
    # Go up until we find a directory containing both 'code' and 'tests'
    # Or simply assume the parent of the 'tests' directory is the root if 'tests' is at root
    # The prompt structure implies:
    # projects/PROJ-040-.../
    #   code/
    #   tests/
    #   data/
    # So if we are in tests/, root is parent.
    return curr.parent

PROJECT_ROOT = get_project_root()

# Add the project root to sys.path so we can import code.utils
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.setup_directories import main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure to test directory creation."""
    # We need to mock the base path used in setup_directories.py
    # Since the script hardcodes "projects/PROJ-040-...", we will run it
    # in a temporary directory and verify the structure there.
    # However, the script uses a relative path.
    # To test effectively, we can change the working directory to tmp_path
    # and expect the script to create the structure there.
    return tmp_path

def test_directory_creation(temp_project_root, monkeypatch):
    """Verify that the script creates the expected directory structure."""
    # Change to the temp directory so the relative path in the script is created there
    monkeypatch.chdir(temp_project_root)
    
    # Run the main function
    result = main()
    
    assert result == 0, "main() should return 0 on success"
    
    base_path = temp_project_root / "projects" / "PROJ-040-robustness-of-statistical-tests-to-data-"
    
    # Verify base path exists
    assert base_path.exists(), "Base project directory should be created"
    
    expected_dirs = [
        "code/data",
        "code/utils",
        "code/viz",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]
    
    for dir_name in expected_dirs:
        full_path = base_path / dir_name
        assert full_path.exists(), f"Directory {dir_name} should exist"
        assert full_path.is_dir(), f"{dir_name} should be a directory"

def test_idempotency(temp_project_root, monkeypatch):
    """Verify that running the script twice doesn't error or duplicate."""
    monkeypatch.chdir(temp_project_root)
    
    # Run first time
    main()
    
    # Run second time
    result = main()
    
    assert result == 0, "Second run should succeed"
    
    base_path = temp_project_root / "projects" / "PROJ-040-robustness-of-statistical-tests-to-data-"
    assert base_path.exists()
    # Check count of directories to ensure no duplicates (though mkdir -p doesn't duplicate)
    # Just verifying the structure is intact
    assert (base_path / "code").exists()
    assert (base_path / "data").exists()
    assert (base_path / "docs").exists()
    assert (base_path / "tests").exists()
