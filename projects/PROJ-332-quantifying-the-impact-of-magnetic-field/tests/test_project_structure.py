import os
from pathlib import Path

def test_required_directories_exist():
    """
    Verify that the required project directories exist.
    
    This test ensures that T001a has been completed successfully
    by checking for the existence of:
    - code/
    - data/raw/
    - data/processed/
    - artifacts/
    - tests/
    """
    base_dir = Path(".")
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "artifacts",
        "tests"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_name} (not a directory)")
    
    assert len(missing_dirs) == 0, f"Missing required directories: {missing_dirs}"