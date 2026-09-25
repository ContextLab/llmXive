"""
Unit tests for the directory structure setup.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from src.setup_data_structure import get_project_root, setup_directories

@pytest.fixture
def mock_project_root():
    """Create a temporary directory to act as a mock project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_project_root_accessible():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_setup_directories_creates_missing(mock_project_root):
    """Test that setup_directories creates the required directories."""
    setup_directories(mock_project_root)

    required_dirs = [
        "src",
        "src/ingestion",
        "src/preprocessing",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state",
    ]

    for dir_name in required_dirs:
        dir_path = mock_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

def test_setup_directories_skips_existing(mock_project_root):
    """Test that setup_directories does not fail if directories already exist."""
    # Create one directory manually
    (mock_project_root / "src").mkdir()
    
    # Run setup again
    setup_directories(mock_project_root)
    
    # Should still exist
    assert (mock_project_root / "src").exists()
    # And all others should be created
    assert (mock_project_root / "tests").exists()
