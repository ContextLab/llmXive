"""
Unit tests for the data directory setup functionality.

These tests verify that the `setup_data_directories` function correctly
creates the required subdirectories (`raw`, `processed`, `interim`)
and their corresponding `.gitkeep` files.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to handle the import path carefully since this test might run
# before the full project structure is established or from different locations.
import sys
import importlib.util

# Helper to load the module dynamically if needed
def load_setup_module():
    spec_path = Path(__file__).parent.parent.parent / "code" / "setup_data_directories.py"
    if not spec_path.exists():
        # Fallback: try to import from code path if available in sys.path
        try:
            from setup_data_directories import setup_data_directories
            return setup_data_directories
        except ImportError:
            pytest.fail("Could not locate setup_data_directories.py")
    
    spec = importlib.util.spec_from_file_location("setup_data_directories", spec_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.setup_data_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate a project root."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_setup_creates_data_directory(temp_project_root):
    """Test that the main data directory is created if it doesn't exist."""
    setup_func = load_setup_module()
    data_dir = temp_project_root / "data"
    
    assert not data_dir.exists()
    
    setup_func(temp_project_root)
    
    assert data_dir.exists()
    assert data_dir.is_dir()

def test_setup_creates_subdirectories(temp_project_root):
    """Test that raw, processed, and interim subdirectories are created."""
    setup_func = load_setup_module()
    subdirs = ["raw", "processed", "interim"]
    
    setup_func(temp_project_root)
    
    for subdir_name in subdirs:
        subdir_path = temp_project_root / "data" / subdir_name
        assert subdir_path.exists()
        assert subdir_path.is_dir()

def test_setup_creates_gitkeep_files(temp_project_root):
    """Test that .gitkeep files are created in each subdirectory."""
    setup_func = load_setup_module()
    subdirs = ["raw", "processed", "interim"]
    
    setup_func(temp_project_root)
    
    for subdir_name in subdirs:
        subdir_path = temp_project_root / "data" / subdir_name
        gitkeep_path = subdir_path / ".gitkeep"
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()
        # Check that the file is empty (or contains only whitespace)
        content = gitkeep_path.read_text()
        assert content.strip() == "", f".gitkeep file should be empty, but contains: {content}"

def test_setup_idempotent(temp_project_root):
    """Test that running setup multiple times doesn't cause errors or duplicate files."""
    setup_func = load_setup_module()
    
    # Run once
    setup_func(temp_project_root)
    
    # Capture initial state
    data_dir = temp_project_root / "data"
    initial_mod_time = data_dir.stat().st_mtime
    
    # Run again
    setup_func(temp_project_root)
    
    # Directory should still exist and not have been recreated (mod time might change due to access, but structure should be stable)
    assert data_dir.exists()
    
    subdirs = ["raw", "processed", "interim"]
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        assert subdir_path.exists()
        gitkeep_path = subdir_path / ".gitkeep"
        assert gitkeep_path.exists()

def test_setup_with_existing_data_directory(temp_project_root):
    """Test that setup works correctly if data directory already exists."""
    setup_func = load_setup_module()
    
    # Pre-create data directory
    data_dir = temp_project_root / "data"
    data_dir.mkdir()
    
    # Run setup
    setup_func(temp_project_root)
    
    # Verify subdirectories were created
    subdirs = ["raw", "processed", "interim"]
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        assert subdir_path.exists()
        gitkeep_path = subdir_path / ".gitkeep"
        assert gitkeep_path.exists()