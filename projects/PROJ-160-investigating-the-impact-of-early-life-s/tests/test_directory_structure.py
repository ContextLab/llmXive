import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Verify that the required subdirectories exist in the project root.
    This test ensures that T001b has been successfully completed.
    """
    # The test assumes it is run from the project root
    project_root = Path.cwd()
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "contracts"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_name} (exists but is not a directory)")
    
    assert len(missing_dirs) == 0, f"Missing or invalid directories: {missing_dirs}"