import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import create_directories, create_gitkeep_files, verify_structure, REQUIRED_DIRS

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_create_directories_creates_all_required(temp_project_root):
    """Test that create_directories creates all required directories."""
    created = create_directories(temp_project_root)
    
    assert len(created) == len(REQUIRED_DIRS), f"Expected {len(REQUIRED_DIRS)} directories, created {len(created)}"
    
    for dir_name in REQUIRED_DIRS:
        target_path = temp_project_root / dir_name
        assert target_path.exists(), f"Directory {target_path} was not created"
        assert target_path.is_dir(), f"{target_path} exists but is not a directory"

def test_create_directories_ignores_existing(temp_project_root):
    """Test that create_directories does not fail if directories already exist."""
    # Pre-create one directory
    pre_created = temp_project_root / REQUIRED_DIRS[0]
    pre_created.mkdir()
    
    created = create_directories(temp_project_root)
    
    # Should only return the ones that were actually created in this call
    # or we can just check that no exception was raised and all exist
    for dir_name in REQUIRED_DIRS:
        target_path = temp_project_root / dir_name
        assert target_path.exists()

def test_create_gitkeep_files(temp_project_root):
    """Test that create_gitkeep_files creates .gitkeep in all directories."""
    # First create the directories
    create_directories(temp_project_root)
    
    created_files = create_gitkeep_files(temp_project_root)
    
    assert len(created_files) == len(REQUIRED_DIRS), f"Expected {len(REQUIRED_DIRS)} .gitkeep files, created {len(created_files)}"
    
    for dir_name in REQUIRED_DIRS:
        target_path = temp_project_root / dir_name / ".gitkeep"
        assert target_path.exists(), f".gitkeep file not created in {target_path.parent}"
        assert target_path.is_file(), f"{target_path} is not a file"

def test_verify_structure_success(temp_project_root):
    """Test verify_structure returns True when structure is complete."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    assert verify_structure(temp_project_root) is True

def test_verify_structure_missing_dir(temp_project_root):
    """Test verify_structure returns False when a directory is missing."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    # Remove one directory
    (temp_project_root / REQUIRED_DIRS[0]).rmdir()
    
    assert verify_structure(temp_project_root) is False

def test_verify_structure_missing_gitkeep(temp_project_root):
    """Test verify_structure returns False when a .gitkeep is missing."""
    create_directories(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    # Remove one .gitkeep
    (temp_project_root / REQUIRED_DIRS[0] / ".gitkeep").unlink()
    
    assert verify_structure(temp_project_root) is False