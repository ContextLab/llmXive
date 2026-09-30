import os
import pytest
from pathlib import Path
import shutil
import tempfile
from setup_structure import create_project_structure, ensure_init_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_project_structure_creates_directories(temp_project_root):
    """Test that all required directories are created."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "tests",
        "state",
        "docs",
        "logs",
        "figures",
    ]

    create_project_structure(temp_project_root)

    for dir_path_str in required_dirs:
        full_path = temp_project_root / dir_path_str
        assert full_path.exists(), f"Directory {dir_path_str} was not created"
        assert full_path.is_dir(), f"{dir_path_str} exists but is not a directory"

def test_create_project_structure_creates_submodules(temp_project_root):
    """Test that __init__.py files are created for Python packages."""
    # First create the structure
    create_project_structure(temp_project_root)
    
    # Then ensure init files
    ensure_init_files(temp_project_root)

    python_package_dirs = [
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "code/utils",
        "tests",
    ]

    for dir_path_str in python_package_dirs:
        full_path = temp_project_root / dir_path_str
        init_file = full_path / "__init__.py"
        
        assert full_path.exists(), f"Directory {dir_path_str} should exist"
        assert init_file.exists(), f"__init__.py missing in {dir_path_str}"
        assert init_file.is_file(), f"{init_file} exists but is not a file"

def test_idempotency(temp_project_root):
    """Test that running the setup twice does not cause errors."""
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    # Run again
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    # Should still exist
    assert (temp_project_root / "data/raw").exists()
    assert (temp_project_root / "code/data" / "__init__.py").exists()
