import os
import pytest
from pathlib import Path
import shutil
import tempfile
import sys

# Add the code directory to the path so we can import setup_directories
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the repository root."""
    temp_dir = tempfile.mkdtemp()
    # Create a 'code' subdirectory to match the expected structure
    (Path(temp_dir) / "code").mkdir()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)

def test_directory_creation(temp_project_root):
    """Test that the main function creates the required directory structure."""
    # Change to the temp directory to simulate running from repo root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run the setup
        result = main()
        
        assert result == 0, "Main function should return 0 on success"
        
        project_name = "PROJ-451-predicting-the-glass-forming-region-of-m"
        project_root = Path(temp_project_root) / "projects" / project_name
        
        # Check root project directory
        assert project_root.exists(), f"Project root {project_root} was not created"
        
        # Check subdirectories
        required_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
            "docs",
            "notebooks",
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
        
        # Check .gitkeep files
        gitkeep_dirs = [
            "data",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
            "docs",
            "notebooks",
        ]
        
        for dir_name in gitkeep_dirs:
            gitkeep_path = project_root / dir_name / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep file {gitkeep_path} was not created"
            assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"
            
    finally:
        os.chdir(original_cwd)

def test_idempotency(temp_project_root):
    """Test that running main twice does not cause errors."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run twice
        result1 = main()
        result2 = main()
        
        assert result1 == 0
        assert result2 == 0
        
    finally:
        os.chdir(original_cwd)
