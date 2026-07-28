import os
import pytest
import tempfile
import shutil
from pathlib import Path

# We need to add the code directory to the path to import the module
# Since this test runs from the project root, we adjust sys.path if needed
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.setup_directories import create_project_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_project_structure_creates_all_dirs(temp_project_root):
    """Verify that create_project_structure creates all required directories."""
    required_dirs = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
        "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot"
    ]
    
    # Run the function
    create_project_structure()
    
    # Verify each directory exists
    for dir_name in required_dirs:
        full_path = os.path.join(temp_project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory {dir_name} was not created at {full_path}"

def test_create_project_structure_idempotent(temp_project_root):
    """Verify that running the function twice does not cause errors."""
    # Run once
    create_project_structure()
    # Run again
    create_project_structure()
    
    # Verify directories still exist
    assert os.path.isdir(os.path.join(temp_project_root, "data/raw"))
    assert os.path.isdir(os.path.join(temp_project_root, "code"))