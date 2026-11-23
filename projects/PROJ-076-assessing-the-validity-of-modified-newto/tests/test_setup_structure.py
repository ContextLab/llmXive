import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from code.setup_structure import create_directories

def test_create_directories_creates_all_required_folders():
    """Test that create_directories creates all required folders."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        create_directories(project_root)
        
        # Check main directories
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "tests",
            "state",
            "code/models",
            "code/utils",
            "code/simulations",
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_create_directories_idempotent():
    """Test that running create_directories twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Run twice
        create_directories(project_root)
        create_directories(project_root)
        
        # Should still exist
        assert (project_root / "code").exists()
        assert (project_root / "data/raw").exists()