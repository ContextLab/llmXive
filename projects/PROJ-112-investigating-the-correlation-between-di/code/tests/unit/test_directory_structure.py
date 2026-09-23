"""
Unit tests for the setup_data_structure module.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from src.setup_data_structure import get_project_root, setup_directories

@pytest.fixture
def mock_project_root():
    """Create a mock project root structure for testing."""
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir)
    # Create minimal structure to satisfy get_project_root heuristics
    (root / ".git").mkdir()
    (root / "src").mkdir()
    (root / "data").mkdir()
    yield root
    shutil.rmtree(temp_dir)

def test_project_root_accessible(mock_project_root):
    """Test that get_project_root correctly identifies the root."""
    # Change to the mock root to simulate running from there
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(mock_project_root)
        detected_root = get_project_root()
        assert detected_root == mock_project_root
    finally:
        os.chdir(original_cwd)

def test_setup_directories_creates_missing(mock_project_root):
    """Test that setup_directories creates directories that do not exist."""
    # Ensure data/raw does not exist
    target = mock_project_root / "data" / "raw"
    assert not target.exists()
    
    setup_directories(mock_project_root)
    
    assert target.exists()
    assert target.is_dir()

def test_setup_directories_skips_existing(mock_project_root):
    """Test that setup_directories does not fail if directories already exist."""
    # Create the directory manually
    target = mock_project_root / "data" / "raw"
    target.mkdir(parents=True, exist_ok=True)
    
    # This should not raise an exception
    setup_directories(mock_project_root)
    
    assert target.exists()
