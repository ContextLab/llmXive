import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Verifies that the core directory structure required by plan.md exists.
    Tests T001a, T001b, T001c, T001d, T002a, T002b.
    """
    base_path = Path.cwd()
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/primes",
        "data/targets",
        "code",
        "tests",
        "state",
        "state/projects/PROJ-345"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)
    
    assert not missing, f"Missing required directories: {missing}"