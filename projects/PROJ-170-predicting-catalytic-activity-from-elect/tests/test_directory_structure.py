"""
Test to verify the existence of required project directories.
This test specifically validates T001e (tests/ directory) and related setup tasks.
"""
import os
import pytest
from pathlib import Path

# Import project root utility
try:
    from config import get_project_root
except ImportError:
    # Fallback if config isn't installed in path yet during standalone run
    from pathlib import Path
    def get_project_root():
        return Path(__file__).resolve().parent.parent

def get_required_directories():
    """Returns a list of required directory paths relative to project root."""
    root = get_project_root()
    return [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "code",
        root / "outputs",
        root / "tests",       # T001e target
        root / "state" / "projects",
        root / "code" / "models",
    ]

def test_all_required_directories_exist():
    """
    Verify that all directories created in Phase 1 (T001a-T001g) exist.
    Specifically checks for the 'tests/' directory (T001e).
    """
    required_dirs = get_required_directories()
    missing_dirs = []

    for dir_path in required_dirs:
        if not dir_path.exists():
            missing_dirs.append(str(dir_path))
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_path} (exists but is not a directory)")

    if missing_dirs:
        pytest.fail(f"The following required directories are missing or invalid:\n"
                    f"{chr(10).join(missing_dirs)}\n"
                    f"Please run the setup scripts to initialize the project structure.")

def test_tests_directory_is_writable():
    """
    Verify that the tests/ directory is writable (sanity check for T001e).
    """
    tests_dir = get_project_root() / "tests"
    assert tests_dir.exists(), "tests/ directory does not exist"
    assert tests_dir.is_dir(), "tests/ is not a directory"
    
    # Attempt to create a temporary marker file
    marker_file = tests_dir / ".write_test_marker"
    try:
        marker_file.touch()
        marker_file.unlink()
    except PermissionError:
        pytest.fail("tests/ directory exists but is not writable.")