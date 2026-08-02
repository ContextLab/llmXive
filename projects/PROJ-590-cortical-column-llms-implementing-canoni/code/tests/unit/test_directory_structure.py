import os
import pytest
import sys
from pathlib import Path

# Define the expected directories based on T001 requirements
# Mapped to code/ root as per project structure
REQUIRED_DIRS = [
    "code/src/models",
    "code/src/data",
    "code/src/training",
    "code/src/experiments",
    "code/src/utils",
    "code/tests/unit",
    "code/tests/integration",
    "code/scripts",
    "code/data/results",
    "code/data/logs",
    "code/data/configs",
    "code/state"
]

def test_project_directories_exist():
    """Verify all required directories from T001 exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            missing.append(str(path))
    
    assert not missing, f"Missing required directories: {missing}"

def test_project_root_is_valid():
    """Verify the project root structure is valid."""
    root = Path("code")
    assert root.exists(), "Project root 'code' does not exist"
    assert root.is_dir(), "Project root 'code' is not a directory"
    
    # Check for essential subdirectories
    assert (root / "src").exists(), "Missing 'code/src'"
    assert (root / "tests").exists(), "Missing 'code/tests'"
    assert (root / "data").exists(), "Missing 'code/data'"
    assert (root / "scripts").exists(), "Missing 'code/scripts'"
    assert (root / "state").exists(), "Missing 'code/state'"
