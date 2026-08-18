import os
import pytest
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def test_required_directories_exist():
    """Test that all required directories defined in T001 exist."""
    root = get_project_root()
    
    required_dirs = [
        "src",
        "tests",
        "contracts",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "reports",
        "specs",
        "state",
        "state/projects"
    ]
    
    for dir_name in required_dirs:
        dir_path = root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_structure_is_writable():
    """Test that the structure allows writing files."""
    root = get_project_root()
    test_file = root / "data" / ".write_test"
    
    try:
        test_file.write_text("test")
        assert test_file.exists()
    finally:
        if test_file.exists():
            test_file.unlink()
