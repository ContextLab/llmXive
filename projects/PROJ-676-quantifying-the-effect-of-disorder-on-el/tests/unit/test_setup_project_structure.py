import pytest
from pathlib import Path
import os
import tempfile
import shutil

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from code.setup_project_structure import create_directories, create_gitkeep_files, verify_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates the expected folder structure."""
    create_directories(temp_project_root)
    
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "specs",
        "specs/001-quantifying-disorder-effect",
        "specs/001-quantifying-disorder-effect/contracts",
        "data/processed/visualizations",
        "figures",
    ]
    
    for d in expected_dirs:
        assert (temp_project_root / d).exists(), f"Directory {d} was not created."

def test_create_gitkeep_files(temp_project_root):
    """Test that create_gitkeep_files creates .gitkeep in required directories."""
    # First create directories
    create_directories(temp_project_root)
    # Then create gitkeeps
    create_gitkeep_files(temp_project_root)
    
    required_gitkeeps = [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/metadata/.gitkeep",
        "docs/.gitkeep",
        "specs/.gitkeep",
    ]
    
    for f in required_gitkeeps:
        file_path = temp_project_root / f
        assert file_path.exists(), f"File {f} was not created."
        assert file_path.is_file(), f"{f} is not a file."

def test_verify_structure_success(temp_project_root):
    """Test verify_structure returns True when everything is present."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    assert verify_structure(temp_project_root) is True

def test_verify_structure_failure_missing_dir(temp_project_root):
    """Test verify_structure returns False when a directory is missing."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    # Remove a directory
    (temp_project_root / "docs").rmdir()
    
    assert verify_structure(temp_project_root) is False

def test_verify_structure_failure_missing_gitkeep(temp_project_root):
    """Test verify_structure returns False when a .gitkeep is missing."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    # Remove a gitkeep
    (temp_project_root / "docs" / ".gitkeep").unlink()
    
    assert verify_structure(temp_project_root) is False
