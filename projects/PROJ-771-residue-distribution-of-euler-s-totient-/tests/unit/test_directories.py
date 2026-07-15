import os
from pathlib import Path
import pytest

def test_required_directories_exist():
    """
    Verifies that the directory structure created by T001a-T001d exists.
    """
    base = Path(".")
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/plots",
        "results/reports",
        "tests/unit",
        "tests/integration"
    ]
    
    for dir_path in required_dirs:
        full_path = base / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} exists but is not a directory"