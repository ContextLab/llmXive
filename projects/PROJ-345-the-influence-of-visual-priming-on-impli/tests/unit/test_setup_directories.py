import os
import pytest
from pathlib import Path
from code.setup_directories import create_directories

def test_create_directories_creates_structure():
    """
    Verifies that create_directories() successfully creates the required
    directory structure defined in plan.md.
    """
    # Expected directories relative to project root
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/primes",
        "data/targets",
        "code",
        "tests",
        "state",
        "state/projects/PROJ-345"
    ]
    
    # Clean up if they exist (optional, for test isolation)
    # In a real CI/CD, this might be handled by the test runner environment
    # We just ensure they exist after the function runs.
    
    result = create_directories()
    
    assert result is True, "create_directories should return True on success"
    
    for dir_name in expected_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Directory {dir_name} should exist after running create_directories"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    # Specifically check the nested project state directory
    proj_state = Path("state/projects/PROJ-345")
    assert proj_state.exists(), "state/projects/PROJ-345 must exist"