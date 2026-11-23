import os
import pytest
from pathlib import Path
import shutil
import tempfile

from code.setup_directories import setup_directories


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate a project root."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


def test_setup_directories_creates_all_required_folders(temp_project_root):
    """Test that setup_directories creates all required directories."""
    setup_directories()
    
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state",
        "templates",
        "docs"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(temp_project_root) / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"


def test_setup_directories_idempotent(temp_project_root):
    """Test that running setup_directories twice doesn't cause errors."""
    # Run first time
    setup_directories()
    
    # Run second time - should not raise errors
    setup_directories()
    
    # Verify directories still exist
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state",
        "templates",
        "docs"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(temp_project_root) / dir_name
        assert dir_path.exists(), f"Directory {dir_name} missing after second run"
