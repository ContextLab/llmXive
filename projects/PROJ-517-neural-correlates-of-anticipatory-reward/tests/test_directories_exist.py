"""
Test to verify that required data directories exist.
Implements verification for Task T001b.
"""
import os
import pytest
from pathlib import Path

def test_data_directories_exist():
    """Assert that data/raw, data/processed, and data/figures exist."""
    # Determine project root relative to this test file
    # Assuming tests/ is at root
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/figures"
    ]
    
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"Path exists but is not a directory: {full_path}"

def test_setup_script_creates_dirs():
    """Verify the setup script creates directories if missing."""
    import subprocess
    import shutil
    
    project_root = Path(__file__).resolve().parent.parent
    test_dir = project_root / "data" / "test_temp_dir"
    
    # Ensure it doesn't exist
    if test_dir.exists():
        shutil.rmtree(test_dir)
        
    # Run the setup script (which creates data dirs)
    # We rely on the fact that the script creates the main dirs.
    # This test primarily ensures the script runs without error.
    result = subprocess.run(
        ["python", "code/setup_directories.py"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"
    
    # Verify the main dirs now exist
    for dir_name in ["data/raw", "data/processed", "data/figures"]:
        assert (project_root / dir_name).exists()