import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from setup_project import create_directories, verify_directories, create_init_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates all required paths."""
    create_directories(temp_project_root)
    
    required_dirs = [
        'data/raw',
        'data/processed',
        'code',
        'outputs',
        'tests',
        'state/projects',
        'code/models'
    ]

    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

def test_verify_directories_success(temp_project_root):
    """Test that verify_directories passes when directories exist."""
    create_directories(temp_project_root)
    # This should not raise an error or exit
    verify_directories(temp_project_root)

def test_verify_directories_failure(temp_project_root):
    """Test that verify_directories fails when a directory is missing."""
    # Create only some directories
    (temp_project_root / 'code').mkdir()
    (temp_project_root / 'outputs').mkdir()
    
    # Remove a required directory if it exists (though it shouldn't)
    missing_dir = temp_project_root / 'data/raw'
    if missing_dir.exists():
        shutil.rmtree(missing_dir)
    
    # Verify should raise SystemExit
    with pytest.raises(SystemExit) as exc_info:
        verify_directories(temp_project_root)
    
    assert exc_info.value.code == 1

def test_create_init_files(temp_project_root):
    """Test that create_init_files creates __init__.py in package directories."""
    create_directories(temp_project_root)
    create_init_files(temp_project_root)
    
    package_dirs = [
        'code',
        'tests',
        'code/utils',
        'code/models'
    ]

    for dir_name in package_dirs:
        init_file = temp_project_root / dir_name / '__init__.py'
        assert init_file.exists(), f"__init__.py missing in {dir_name}"