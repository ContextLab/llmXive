"""
Tests for the init_dirs script.
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.init_dirs import get_project_root, create_directories, write_init_log

def test_get_project_root():
    """Test that get_project_root returns a valid Path."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_create_directories():
    """Test that create_directories creates all required directories."""
    created_paths = create_directories()
    
    # Check that all expected directories were created
    expected_dirs = [
        "code",
        "data",
        "data/synthetic",
        "data/synthetic/raw",
        "data/synthetic/short_context",
        "data/results",
        "data/results/logs",
        "data/results/aggregated",
        "tests",
        "models",
        "data/assets",
    ]
    
    assert len(created_paths) == len(expected_dirs)
    
    root = get_project_root()
    for expected in expected_dirs:
        full_path = root / expected
        assert full_path.exists()
        assert full_path.is_dir()

def test_write_init_log():
    """Test that write_init_log creates the log file."""
    created_paths = create_directories()
    log_path = write_init_log(created_paths)
    
    assert log_path.exists()
    assert log_path.is_file()
    
    content = log_path.read_text()
    assert "Initialization completed" in content
    assert "Created" in content
    assert "directories" in content

def test_full_workflow():
    """Test the complete workflow of directory initialization."""
    # Clean up any existing log file for a fresh test
    root = get_project_root()
    log_path = root / "data" / ".init_log.txt"
    if log_path.exists():
        log_path.unlink()
    
    # Run the main workflow
    created = create_directories()
    written_log = write_init_log(created)
    
    # Verify log file exists and has content
    assert written_log.exists()
    assert written_log.read_text().strip() != ""