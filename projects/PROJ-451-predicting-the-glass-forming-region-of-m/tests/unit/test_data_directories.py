"""
Unit tests to verify the data directory structure setup.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to import the function from the script we just created
# Adjusting import path based on project structure
import sys
import importlib.util

# Load setup_data_directories module dynamically to ensure we test the actual file
script_path = Path(__file__).parent.parent.parent / "code" / "setup_data_directories.py"
spec = importlib.util.spec_from_file_location("setup_data_directories", script_path)
setup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_module)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that the script creates the required directories."""
    # Run the setup logic
    setup_module.create_directory_structure(temp_project_root)
    
    # Check that directories exist
    data_root = temp_project_root / "data"
    assert data_root.exists(), "data/ directory should exist"
    
    required_dirs = ["raw", "processed", "interim", "results"]
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        assert dir_path.exists(), f"{dir_name}/ directory should exist"
        assert dir_path.is_dir(), f"{dir_name}/ should be a directory"

def test_gitkeep_files_created(temp_project_root):
    """Test that .gitkeep files are created in each data subdirectory."""
    setup_module.create_directory_structure(temp_project_root)
    
    data_root = temp_project_root / "data"
    required_dirs = ["raw", "processed", "interim", "results"]
    
    for dir_name in required_dirs:
        gitkeep_path = data_root / dir_name / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep should exist in {dir_name}/"
        assert gitkeep_path.is_file(), f".gitkeep in {dir_name}/ should be a file"
        
        # Check content is not empty
        content = gitkeep_path.read_text()
        assert len(content) > 0, f".gitkeep in {dir_name}/ should have content"

def test_no_error_on_existing_dirs(temp_project_root):
    """Test that the script handles existing directories gracefully."""
    # Pre-create the directories
    data_root = temp_project_root / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "raw").mkdir(exist_ok=True)
    (data_root / "processed").mkdir(exist_ok=True)
    (data_root / "interim").mkdir(exist_ok=True)
    (data_root / "results").mkdir(exist_ok=True)
    
    # Run the setup logic - should not raise an error
    setup_module.create_directory_structure(temp_project_root)
    
    # Verify directories still exist
    assert (data_root / "raw").exists()
    assert (data_root / "processed").exists()