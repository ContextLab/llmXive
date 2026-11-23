"""
Verification test for Task T001a.
Ensures the directory structure required by the project plan exists.
"""
import os
from pathlib import Path
import pytest

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/models",
    "tests/unit",
    "tests/integration",
    "results",
]

def test_project_directory_structure_exists():
    """
    Asserts that all directories defined in T001a exist relative to the project root.
    """
    root = Path.cwd()
    missing = []
    
    for dir_name in REQUIRED_DIRS:
        full_path = root / dir_name
        if not full_path.exists():
            missing.append(dir_name)
        elif not full_path.is_dir():
            missing.append(f"{dir_name} (not a directory)")
    
    assert not missing, f"Missing required directories: {missing}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])