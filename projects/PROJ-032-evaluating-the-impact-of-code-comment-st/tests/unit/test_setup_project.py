"""
Tests for Task T001: Project structure creation.
"""
import os
import pytest
import tempfile
import shutil
import sys

# Add src to path to allow import if needed, though we test via side effects mostly
# For this specific task, we are testing the filesystem side effects of the script
# or the logic if refactored into a module.

# Since the script is standalone, we will test the directory creation logic
# by importing the function if we refactor, or by checking the filesystem
# after running the script. 

# To strictly follow the "extend existing API" and "import real names" rule,
# we assume the function `create_directories` is the target. 
# However, the script provided is a standalone entry point. 
# We will test the existence of the directories after execution.

# We will mock the script execution in a temp directory to ensure isolation.

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate the project root."""
    # Change to the temp directory to run the script logic safely
    original_cwd = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(tmp_path)
    os.chdir(original_cwd)

def test_directory_structure_created(temp_project_root):
    """Verify that the expected directories are created."""
    # Import the logic to test. 
    # Since the script is in code/setup_project.py, we need to import it.
    # We add the parent of 'code' to sys.path? No, 'code' is inside the project.
    # We assume the script is run from the project root.
    
    # Let's import the function by adding the 'code' directory to path?
    # Actually, the script is `code/setup_project.py`.
    # We can import it if we add the root to path.
    
    sys.path.insert(0, '.') 
    from code.setup_project import create_directories
    
    create_directories()

    expected_dirs = [
        "src/code",
        "src/data/raw",
        "src/data/processed",
        "src/data/schemas",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    for dir_path in expected_dirs:
        full_path = os.path.join(temp_project_root, dir_path)
        assert os.path.isdir(full_path), f"Directory {dir_path} was not created."

def test_idempotency(temp_project_root):
    """Verify that running the script twice does not raise errors."""
    sys.path.insert(0, '.')
    from code.setup_project import create_directories
    
    # Run twice
    create_directories()
    create_directories()
    
    # Check one directory still exists
    assert os.path.isdir(os.path.join(temp_project_root, "src/code"))