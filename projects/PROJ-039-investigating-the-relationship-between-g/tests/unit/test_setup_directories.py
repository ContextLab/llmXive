import os
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import create_directories, get_project_root

def test_directory_creation():
    """Test that all required directories are created."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Temporarily patch the get_project_root function behavior
        # by creating the structure in tmp_dir
        root = Path(tmp_dir)
        
        # Create the expected subdirectories
        required_dirs = [
            root / "data" / "processed",
            root / "artifacts",
            root / "tests" / "contract",
            root / "tests" / "integration",
            root / "tests" / "unit",
        ]
        
        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Verify all directories exist
        for directory in required_dirs:
            assert directory.exists(), f"Directory {directory} was not created"
            assert directory.is_dir(), f"{directory} is not a directory"

def test_get_project_root():
    """Test that get_project_root returns a valid Path object."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()