import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Verify that all required project directories exist.
    This test ensures T001 requirements are met.
    """
    base_dir = Path(".")
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state",
        "results",
        "contracts"
    ]
    
    missing = []
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.is_dir():
            missing.append(dir_name)
    
    assert len(missing) == 0, f"Missing required directories: {missing}"

def test_data_subdirectories_exist():
    """
    Verify that data/raw and data/processed exist specifically.
    """
    base_dir = Path(".")
    
    assert (base_dir / "data" / "raw").is_dir(), "data/raw must exist"
    assert (base_dir / "data" / "processed").is_dir(), "data/processed must exist"
