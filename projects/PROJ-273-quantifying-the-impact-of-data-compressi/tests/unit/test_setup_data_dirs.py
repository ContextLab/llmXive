import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

def test_setup_data_directories_creates_structure():
    """Test that setup_data_directories creates the required directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Run the setup function
        setup_data_directories(project_root)
        
        # Verify the base data directory exists
        data_dir = project_root / "data"
        assert data_dir.exists(), "Base data directory should exist"
        assert data_dir.is_dir(), "Base data directory should be a directory"
        
        # Verify all required subdirectories exist
        required_subdirs = ["raw", "interim", "processed", "external"]
        for subdir in required_subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir} should exist"
            assert subdir_path.is_dir(), f"Subdirectory {subdir} should be a directory"

def test_setup_data_directories_idempotent():
    """Test that running setup_data_directories multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Run the setup function twice
        setup_data_directories(project_root)
        setup_data_directories(project_root)
        
        # Verify the structure still exists and is correct
        data_dir = project_root / "data"
        assert data_dir.exists(), "Base data directory should exist after multiple runs"
        
        required_subdirs = ["raw", "interim", "processed", "external"]
        for subdir in required_subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir} should exist after multiple runs"

def test_setup_data_directories_with_custom_root():
    """Test that setup_data_directories works with a custom project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "custom_root"
        project_root.mkdir()
        
        # Run the setup function with custom root
        setup_data_directories(project_root)
        
        # Verify the structure exists in the custom root
        data_dir = project_root / "data"
        assert data_dir.exists(), "Data directory should exist in custom root"
        
        required_subdirs = ["raw", "interim", "processed", "external"]
        for subdir in required_subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir} should exist in custom root"