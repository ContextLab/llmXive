import os
import pytest
from pathlib import Path
import shutil
import tempfile
from setup_structure import create_project_structure, ensure_init_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_project_structure_creates_directories(temp_project_root):
    """Test that create_project_structure creates all required directories."""
    create_project_structure(temp_project_root)
    
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
    ]
    
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_create_project_structure_creates_submodules(temp_project_root):
    """Test that ensure_init_files creates __init__.py files in all package directories."""
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    package_dirs = [
        "code",
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "tests",
    ]
    
    for dir_name in package_dirs:
        dir_path = temp_project_root / dir_name
        init_file = dir_path / "__init__.py"
        assert init_file.exists(), f"__init__.py not found in {dir_path}"
        assert init_file.is_file(), f"{init_file} is not a file"

def test_idempotency(temp_project_root):
    """Test that running the setup functions multiple times doesn't cause errors."""
    # First run
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    # Second run - should not raise any exceptions
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    # Verify directories still exist
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
    ]
    
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} missing after second run"