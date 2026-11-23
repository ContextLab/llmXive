import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_project_structure import create_directories, create_gitkeep_files, verify_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates the expected folder structure."""
    dirs = create_directories(temp_project_root)
    
    expected_subdirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "specs/001-quantifying-disorder-effect/contracts",
    ]
    
    for subdir in expected_subdirs:
        full_path = temp_project_root / subdir
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} is not a directory."

def test_create_gitkeep_files(temp_project_root):
    """Test that create_gitkeep_files creates .gitkeep in required directories."""
    # Ensure directories exist first
    create_directories(temp_project_root)
    
    gitkeeps = create_gitkeep_files(temp_project_root)
    
    required_gitkeeps = [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/metadata/.gitkeep",
        "docs/.gitkeep",
        "specs/001-quantifying-disorder-effect/contracts/.gitkeep",
    ]
    
    for rel_path in required_gitkeeps:
        full_path = temp_project_root / rel_path
        assert full_path.exists(), f".gitkeep file {full_path} was not created."
        assert full_path.is_file(), f"{full_path} is not a file."

def test_verify_structure_success(temp_project_root):
    """Test verify_structure returns True when everything is present."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    assert verify_structure(temp_project_root) is True

def test_verify_structure_missing_dir(temp_project_root):
    """Test verify_structure returns False when a directory is missing."""
    create_directories(temp_project_root)
    # Remove one directory
    (temp_project_root / "docs").rmdir()
    
    assert verify_structure(temp_project_root) is False

def test_verify_structure_missing_gitkeep(temp_project_root):
    """Test verify_structure returns False when a .gitkeep is missing."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    # Remove one gitkeep
    (temp_project_root / "docs" / ".gitkeep").unlink()
    
    assert verify_structure(temp_project_root) is False
