import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    T001a Verification: Ensure all required project directories exist.
    """
    base_dir = Path.cwd()
    required_dirs = [
        "data/raw",
        "data/derived",
        "code",
        "tests",
        "docs",
        "state",
        "contracts",
        "results"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)
    
    assert not missing, f"Missing required directories: {missing}"