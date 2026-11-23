import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import ensure_directory, create_gitkeep
from setup_directories import setup_data_and_results_directories

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root for testing."""
    return tmp_path

def test_setup_data_directories_creates_folders(temp_project_root):
    """Test that setup_data_and_results_directories creates the required folders."""
    results = setup_data_and_results_directories(temp_project_root)
    
    # Check that we got results for all 3 directories
    assert len(results) == 3
    
    # Check specific paths exist
    paths = [r[0] for r in results]
    assert temp_project_root / "data" / "raw" in paths
    assert temp_project_root / "data" / "processed" in paths
    assert temp_project_root / "results" in paths
    
    # Check status is not failed
    for path, status in results:
        assert status != "failed", f"Failed to create {path}"

def test_gitkeep_files_created(temp_project_root):
    """Test that .gitkeep files are created in the new directories."""
    setup_data_and_results_directories(temp_project_root)
    
    gitkeep_paths = [
        temp_project_root / "data" / "raw" / ".gitkeep",
        temp_project_root / "data" / "processed" / ".gitkeep",
        temp_project_root / "results" / ".gitkeep",
    ]
    
    for gitkeep_path in gitkeep_paths:
        assert gitkeep_path.exists(), f".gitkeep missing at {gitkeep_path}"
        assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

def test_ensure_directory_creates_parent_directories(temp_project_root):
    """Test that ensure_directory creates parent directories if they don't exist."""
    deep_path = temp_project_root / "data" / "raw" / "subdir"
    success = ensure_directory(deep_path)
    
    assert success
    assert deep_path.exists()
    assert deep_path.is_dir()

def test_create_gitkeep_on_existing_directory(temp_project_root):
    """Test that create_gitkeep works when directory already exists."""
    # Create directory first
    test_dir = temp_project_root / "test_dir"
    test_dir.mkdir()
    
    gitkeep_path = test_dir / ".gitkeep"
    created = create_gitkeep(gitkeep_path)
    
    assert created
    assert gitkeep_path.exists()
    
    # Create again (idempotent)
    created_again = create_gitkeep(gitkeep_path)
    assert created_again  # Should return True even if file exists (idempotent behavior)