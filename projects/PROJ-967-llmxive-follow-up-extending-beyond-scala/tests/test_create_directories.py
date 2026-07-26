import os
import pytest
from pathlib import Path
import shutil

from code.create_directories import ensure_directory, main

PROJECT_ROOT = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")

@pytest.fixture(scope="module")
def setup_project_root():
    """Create the project root directory if it doesn't exist."""
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup: Remove the project root and all its contents after tests
    if PROJECT_ROOT.exists():
        shutil.rmtree(PROJECT_ROOT)

def test_ensure_directory_creates_new_dir(setup_project_root):
    """Test that ensure_directory creates a new directory."""
    test_dir = PROJECT_ROOT / "test_new_dir"
    assert not test_dir.exists()
    
    ensure_directory(test_dir)
    
    assert test_dir.exists()
    assert test_dir.is_dir()

def test_ensure_directory_existing_dir(setup_project_root):
    """Test that ensure_directory does not fail on existing directory."""
    existing_dir = PROJECT_ROOT / "data"
    existing_dir.mkdir(parents=True, exist_ok=True)
    
    # Should not raise an exception
    ensure_directory(existing_dir)
    
    assert existing_dir.exists()

def test_main_creates_all_required_directories(setup_project_root):
    """Test that main() creates all required directories."""
    # Run the main function
    main()
    
    # Define expected directories
    expected_dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "results"
    ]
    
    # Verify all directories exist
    for dir_path in expected_dirs:
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"