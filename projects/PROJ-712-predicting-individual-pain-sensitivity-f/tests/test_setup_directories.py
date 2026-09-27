import os
import pytest
from pathlib import Path
import shutil
import tempfile
import sys

# Add the code directory to the path so we can import the module
# We assume the test is run from the project root or the script is in the same directory structure
# Since the script is at code/setup_directories.py, we need to adjust sys.path
# However, for this specific task, we are testing the creation of directories.
# We will mock the current working directory to ensure we don't mess up the real project structure during tests.

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure mimicking the project root."""
    # Create the base project path
    project_path = tmp_path / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f"
    project_path.mkdir(parents=True)
    return project_path

def test_creates_required_directories(temp_project_root, monkeypatch):
    """
    Test that setup_directories.py creates 'code' and 'tests' directories.
    Also verifies 'data/raw', 'data/processed', 'artifacts', 'state' are created.
    """
    # Change the working directory to the temp project root parent
    # so that the script creates the structure inside temp_project_root
    monkeypatch.chdir(temp_project_root.parent)

    # Import the main function from the script
    # We need to add the code directory to the path
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    # Since the script uses Path.cwd(), we must ensure the cwd is correct
    # The script expects to run from the root of the repo, creating "projects/..."
    # So we are already in the correct place relative to temp_project_root.parent
    
    from setup_directories import main

    # Execute the main function
    result = main()

    # Assert the function returned 0 (success)
    assert result == 0

    # Verify the directories exist
    expected_dirs = [
        "code",
        "tests",
        "data" / "raw",
        "data" / "processed",
        "artifacts",
        "state"
    ]

    for dir_name in expected_dirs:
        full_path = temp_project_root / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} exists but is not a directory"

def test_idempotency(temp_project_root, monkeypatch):
    """
    Test that running the script twice does not raise errors.
    """
    monkeypatch.chdir(temp_project_root.parent)
    
    # Add code to path
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    from setup_directories import main

    # Run twice
    result1 = main()
    result2 = main()

    assert result1 == 0
    assert result2 == 0
    
    # Verify directories still exist
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "tests").exists()