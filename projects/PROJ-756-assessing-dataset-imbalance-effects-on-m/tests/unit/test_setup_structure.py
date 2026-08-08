import os
import sys
import pytest
from pathlib import Path
import shutil

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import create_directories

PROJECT_ROOT = Path("projects/PROJ-756-assessing-dataset-imbalance-effects-on-m")

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Ensure clean state before and after tests."""
    # Cleanup if exists
    if PROJECT_ROOT.exists():
        shutil.rmtree(PROJECT_ROOT)
    
    yield
    
    # Cleanup after test
    if PROJECT_ROOT.exists():
        shutil.rmtree(PROJECT_ROOT)

def test_create_directories_creates_all_folders():
    """Test that create_directories creates all required folders."""
    success = create_directories()
    assert success is True
    
    required_paths = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "artifacts",
        PROJECT_ROOT / "results",
        PROJECT_ROOT / "state",
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "logs" / "archive",
    ]
    
    for path in required_paths:
        assert path.exists(), f"Directory {path} was not created"
        assert path.is_dir(), f"{path} exists but is not a directory"

def test_create_directories_idempotent():
    """Test that running create_directories twice does not fail."""
    # Run once
    create_directories()
    
    # Run again - should not raise error
    success = create_directories()
    assert success is True

def test_project_root_exists():
    """Test that the main project root directory exists."""
    create_directories()
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()
