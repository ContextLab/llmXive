import os
from pathlib import Path

def test_required_directories_exist():
    """Verify that all required project directories exist."""
    root = Path(__file__).resolve().parent.parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/curated",
        "data/results",
        "tests/unit",
        "tests/contract",
        "contracts",
        "docs",
        "paper",
        "state",
        "figures",
    ]
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_config_files_exist():
    """Verify that configuration files exist."""
    root = Path(__file__).resolve().parent.parent.parent
    
    required_files = [
        "code/pyproject.toml",
        "code/requirements.txt",
        "docs/quickstart.md",
    ]
    
    for file_path in required_files:
        full_path = root / file_path
        assert full_path.exists(), f"File {file_path} does not exist"
        assert full_path.is_file(), f"{file_path} is not a file"
