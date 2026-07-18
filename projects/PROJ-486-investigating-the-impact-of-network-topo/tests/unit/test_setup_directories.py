"""
Unit tests for the directory setup and gitkeep initialization scripts.
Verifies that T001b and T001c artifacts are correctly generated.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from setup_directories import create_directories
from setup_gitkeep import initialize_gitkeeps

@pytest.fixture
def temp_project_root():
    """Creates a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_directories_structure(temp_project_root):
    """Tests that create_directories creates all required subdirectories."""
    create_directories()

    required_dirs = [
        "code", "data", "data/raw", "data/processed", "data/visualizations",
        "tests", "tests/unit", "tests/integration", "docs"
    ]

    for dir_name in required_dirs:
        full_path = os.path.join(temp_project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory {dir_name} was not created."

def test_initialize_gitkeeps(temp_project_root):
    """Tests that initialize_gitkeeps creates .gitkeep files in all directories."""
    # First create the directories
    create_directories()
    
    # Then initialize gitkeeps
    initialize_gitkeeps()

    required_dirs = [
        "code", "data", "data/raw", "data/processed", "data/visualizations",
        "tests", "tests/unit", "tests/integration", "docs"
    ]

    for dir_name in required_dirs:
        full_path = os.path.join(temp_project_root, dir_name)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        assert os.path.isfile(gitkeep_path), f".gitkeep missing in {dir_name}"

def test_idempotency(temp_project_root):
    """Tests that running the scripts multiple times does not cause errors."""
    # Run twice
    create_directories()
    create_directories()
    initialize_gitkeeps()
    initialize_gitkeeps()

    # Verify structure still exists
    assert os.path.isdir(os.path.join(temp_project_root, "code"))
    assert os.path.isfile(os.path.join(temp_project_root, "code", ".gitkeep"))