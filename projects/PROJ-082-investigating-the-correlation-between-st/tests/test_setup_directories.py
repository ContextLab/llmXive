import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories, verify_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates all required directories."""
    create_directories(temp_project_root)
    
    required_dirs = [
        "code",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "data/derived",
        "data/config",
        "data/logs",
        "figures"
    ]
    
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_verify_structure_success(temp_project_root):
    """Test verify_structure returns True when all directories exist."""
    create_directories(temp_project_root)
    assert verify_structure(temp_project_root) is True

def test_verify_structure_failure(temp_project_root):
    """Test verify_structure returns False when directories are missing."""
    # Create only one directory
    (temp_project_root / "code").mkdir()
    
    assert verify_structure(temp_project_root) is False

def test_create_directories_idempotent(temp_project_root):
    """Test that calling create_directories multiple times doesn't raise errors."""
    create_directories(temp_project_root)
    create_directories(temp_project_root)
    
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "data/raw").exists()