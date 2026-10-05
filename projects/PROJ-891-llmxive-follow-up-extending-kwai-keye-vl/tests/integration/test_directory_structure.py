import os
import pytest
from pathlib import Path

def test_directory_structure_requirements():
    """
    Integration test to verify that the source directory structure
    (src/generators, src/inference, src/analysis) exists and is accessible.
    """
    project_root = Path(__file__).parent.parent.parent.resolve()
    
    required_dirs = [
        "src/generators",
        "src/inference",
        "src/analysis"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if not full_path.exists():
            missing_dirs.append(dir_name)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_name} (not a directory)")
    
    assert len(missing_dirs) == 0, f"Required source directories are missing: {missing_dirs}"