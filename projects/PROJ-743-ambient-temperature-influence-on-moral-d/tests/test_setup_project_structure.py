import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from setup_project_structure import ensure_directories

def test_ensure_directories_creates_all_required_dirs():
    """Test that ensure_directories creates all required project directories."""
    # Create a temporary directory to act as project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Expected directories relative to project root
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results/figures",
            "results/logs",
            "results/stats",
            "tests",
        ]
        
        # Call the function
        ensure_directories(project_root)
        
        # Verify each directory was created
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_ensure_directories_idempotent():
    """Test that running ensure_directories multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Run twice
        ensure_directories(project_root)
        ensure_directories(project_root)
        
        # Verify directories still exist
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results/figures",
            "results/logs",
            "results/stats",
            "tests",
        ]
        
        for dir_name in expected_dirs:
            assert (project_root / dir_name).exists()

def test_nested_directories_created():
    """Test that nested directories (e.g., data/raw) are created correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        ensure_directories(project_root)
        
        # Check nested structure
        assert (project_root / "data").exists()
        assert (project_root / "data" / "raw").exists()
        assert (project_root / "data" / "processed").exists()
        assert (project_root / "results").exists()
        assert (project_root / "results" / "figures").exists()
        assert (project_root / "results" / "logs").exists()
        assert (project_root / "results" / "stats").exists()