"""
Test for T004: Verify that data subdirectories exist with .gitkeep files.
"""
import os
from pathlib import Path

def test_data_subdirectories_exist():
    """Verify that raw, processed, and interim subdirectories exist under data/."""
    base_path = Path(__file__).parent.parent / "data"
    
    required_dirs = ["raw", "processed", "interim"]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"
        
        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file missing in {dir_path}"
        assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

def test_gitkeep_files_not_empty():
    """Verify that .gitkeep files are not empty (contain at least a comment)."""
    base_path = Path(__file__).parent.parent / "data"
    
    for dir_name in ["raw", "processed", "interim"]:
        gitkeep_path = base_path / dir_name / ".gitkeep"
        content = gitkeep_path.read_text()
        assert len(content.strip()) > 0, f"{gitkeep_path} is empty"