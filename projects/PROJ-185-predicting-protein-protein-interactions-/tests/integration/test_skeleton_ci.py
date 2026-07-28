"""
Integration test for T001d: CI step that fails if any skeleton directory is missing.

This test verifies the presence of required repository skeleton directories.
If any directory is missing, the test fails, causing the CI job to fail.

Required directories (per T001):
- src/
- tests/
- data/
- results/
- docs/
- contracts/
"""
import subprocess
import sys
from pathlib import Path
from check_skeleton import missing_directories


def test_directories_exist():
    """
    Verify that all required skeleton directories exist.
    
    This test implements the T001d requirement: a CI step that fails if any
    skeleton directory is missing. It uses the existing `check_skeleton` module
    to determine which directories are missing.
    
    Raises:
        AssertionError: If any required directories are missing.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    missing = missing_directories(project_root)
    
    if missing:
        missing_str = ", ".join(missing)
        raise AssertionError(
            f"Required skeleton directories are missing: {missing_str}. "
            f"Please run `python code/create_skeleton.py` to initialize the repository structure."
        )
    
    # If we reach here, all directories exist
    print("All required skeleton directories are present.")
    return True
