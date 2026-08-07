import os
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add the parent directory to the path to import setup_project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project import create_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_create_directories_structure(temp_project_root):
    """
    Test that create_directories creates the expected directory structure.
    """
    # Change to the temporary directory to simulate running from project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Call the function
        result = create_directories()
        
        # Assert the function returned True
        assert result is True, "create_directories should return True on success"
        
        # Define expected directories
        expected_dirs = [
            "src/data",
            "src/models",
            "src/analysis",
            "data/raw",
            "data/processed",
            "data/interim",
            "tests/contract",
            "tests/unit",
            "tests/integration",
            "docs"
        ]
        
        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = Path(temp_project_root) / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
            
    finally:
        os.chdir(original_cwd)

def test_create_directories_idempotent(temp_project_root):
    """
    Test that running create_directories twice does not cause errors.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run twice
        result1 = create_directories()
        result2 = create_directories()
        
        assert result1 is True
        assert result2 is True
        
    finally:
        os.chdir(original_cwd)