import os
from pathlib import Path
import pytest
from code.setup_data_dirs import create_data_directories

def test_data_directories_created(tmp_path, monkeypatch):
    """
    Test that create_data_directories creates the required subdirectories.
    """
    # Change working directory to tmp_path to avoid polluting the real project root
    monkeypatch.chdir(tmp_path)
    
    # Run the function
    create_data_directories()
    
    # Verify directories exist
    base_dir = tmp_path / "data"
    assert base_dir.exists(), "Base data directory should exist"
    
    subdirs = ["raw", "intermediate", "processed"]
    for subdir in subdirs:
        dir_path = base_dir / subdir
        assert dir_path.exists(), f"Directory {dir_path} should exist"
        assert dir_path.is_dir(), f"{dir_path} should be a directory"
        
        # Verify .gitkeep exists to track empty directories in git
        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep should exist in {dir_path}"