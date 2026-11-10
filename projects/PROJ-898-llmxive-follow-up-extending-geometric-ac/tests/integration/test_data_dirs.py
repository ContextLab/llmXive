"""
Integration tests to verify that the data directory structure 
and .gitkeep files are correctly created (Task T004).
"""
import os
from pathlib import Path
from llmxive_toolkit import paths

def test_data_directories_and_gitkeeps_exist():
    """
    Assert that the required data directories exist and contain .gitkeep files.
    """
    required_subdirs = ["raw", "generated", "results"]
    
    for subdir in required_subdirs:
        # Construct the expected path relative to project root
        # paths.data(subdir) should resolve to <root>/data/<subdir>
        dir_path = paths.data(subdir)
        gitkeep_file = dir_path / ".gitkeep"
        
        # Verify directory exists
        assert dir_path.exists(), f"Directory {dir_path} should exist"
        assert dir_path.is_dir(), f"Path {dir_path} should be a directory"
        
        # Verify .gitkeep file exists
        assert gitkeep_file.exists(), f".gitkeep file should exist at {gitkeep_file}"
        assert gitkeep_file.is_file(), f"Path {gitkeep_file} should be a file"
        
        # Verify .gitkeep is empty
        assert gitkeep_file.stat().st_size == 0, f".gitkeep file at {gitkeep_file} should be empty"

def test_data_root_exists():
    """
    Verify the top-level data directory exists.
    """
    data_root = paths.data() # Should return <root>/data
    assert data_root.exists(), "Top-level data directory should exist"
    assert data_root.is_dir(), "Top-level data directory should be a directory"