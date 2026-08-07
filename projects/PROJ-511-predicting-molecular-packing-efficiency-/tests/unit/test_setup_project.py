import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the function to test
from setup_project import create_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_directories_structure(temp_project_root):
    """Test that create_directories creates all required folders."""
    required_dirs = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
    ]
    
    create_directories(temp_project_root)
    
    for dir_name in required_dirs:
        dir_path = Path(temp_project_root) / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory"

def test_create_directories_idempotent(temp_project_root):
    """Test that running create_directories twice does not cause errors."""
    required_dirs = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
    ]
    
    # First run
    create_directories(temp_project_root)
    
    # Second run should not raise an error
    create_directories(temp_project_root)
    
    # Verify all directories still exist
    for dir_name in required_dirs:
        dir_path = Path(temp_project_root) / dir_name
        assert dir_path.exists() and dir_path.is_dir()

def test_create_directories_nested(temp_project_root):
    """Test that nested directories (like data/raw_cif) are created correctly."""
    create_directories(temp_project_root)
    
    raw_cif_path = Path(temp_project_root) / "data" / "raw_cif"
    assert raw_cif_path.exists()
    assert raw_cif_path.is_dir()
    
    # Verify parent 'data' also exists
    data_path = Path(temp_project_root) / "data"
    assert data_path.exists()
    assert data_path.is_dir()