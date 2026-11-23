"""
Tests for the setup_directories script.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_directories import PROJECT_ROOT, DIRECTORIES

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    # Adjust the project root path for the temp directory
    original_root = PROJECT_ROOT
    new_root = Path(temp_dir) / "projects" / "PROJ-120-machine-learning-prediction-of-glass-tra"
    
    # Temporarily override the global constant
    import setup_directories
    setup_directories.PROJECT_ROOT = new_root
    setup_directories.DIRECTORIES = [
        new_root,
        new_root / "data",
        new_root / "code",
        new_root / "tests",
        new_root / "artifacts",
        new_root / "state",
    ]
    
    yield new_root
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    # Restore original
    setup_directories.PROJECT_ROOT = original_root
    setup_directories.DIRECTORIES = [
        original_root,
        original_root / "data",
        original_root / "code",
        original_root / "tests",
        original_root / "artifacts",
        original_root / "state",
    ]

def test_directories_created(temp_project_root):
    """Test that all required directories are created."""
    # Run the main logic
    from setup_directories import main
    main()
    
    # Verify each directory exists
    for dir_path in DIRECTORIES:
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_project_root_exists(temp_project_root):
    """Test that the main project root exists."""
    from setup_directories import main
    main()
    
    assert temp_project_root.exists()
    assert temp_project_root.is_dir()

def test_subdirectories_exist(temp_project_root):
    """Test that all required subdirectories exist."""
    from setup_directories import main
    main()
    
    required_subdirs = ["data", "code", "tests", "artifacts", "state"]
    for subdir in required_subdirs:
        dir_path = temp_project_root / subdir
        assert dir_path.exists(), f"Subdirectory {subdir} was not created"
        assert dir_path.is_dir(), f"{subdir} is not a directory"