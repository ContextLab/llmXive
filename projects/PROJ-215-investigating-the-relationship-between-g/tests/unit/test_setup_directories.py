import os
import shutil
import tempfile
import pytest
import sys

# Adjust path to import from the project root if running from tests/
# Assuming tests are run from project root or sys.path includes root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from code.setup_directories import main

@pytest.fixture
def temp_project_root(tmp_path):
    """
    Creates a temporary directory structure to simulate the project root.
    We will change into this directory to run the script safely.
    """
    # Save current directory
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_dir)

def test_creates_code_directories(temp_project_root):
    """
    Test that main() creates code/, code/models/, and code/utils/
    """
    # Ensure they don't exist yet
    assert not os.path.exists("code")
    
    # Run the script
    exit_code = main()
    
    # Assert success
    assert exit_code == 0
    
    # Assert directories were created
    assert os.path.isdir("code")
    assert os.path.isdir("code/models")
    assert os.path.isdir("code/utils")

def test_handles_existing_directories(temp_project_root):
    """
    Test that main() handles the case where directories already exist gracefully.
    """
    # Pre-create the directories
    os.makedirs("code/models", exist_ok=True)
    
    # Run the script
    exit_code = main()
    
    # Should still succeed (return 0)
    assert exit_code == 0
    
    # Directories should still exist
    assert os.path.isdir("code")
    assert os.path.isdir("code/models")
    assert os.path.isdir("code/utils")