import os
import pytest
from pathlib import Path

def get_project_root():
    """Return the project root directory."""
    # Assume the test is run from the project root or a subdirectory
    return Path(__file__).resolve().parent.parent.parent

def test_required_directories_exist():
    """Assert that all required directories for the project structure exist."""
    root = get_project_root()
    required_dirs = [
        'src',
        'tests',
        'contracts',
        'data',
        'data/raw',
        'data/processed',
        'data/logs',
        'reports',
        'state',
        'state/projects'
    ]
    for dir_path in required_dirs:
        full_path = root / dir_path
        assert full_path.is_dir(), f"Directory {full_path} does not exist."

def test_structure_is_writable():
    """Assert that the required directories are writable."""
    root = get_project_root()
    test_file_name = ".write_test_marker"
    try:
        # Test writing to data/processed as a representative directory
        test_path = root / 'data' / 'processed' / test_file_name
        test_path.touch()
        assert test_path.exists(), "Failed to create test file in data/processed."
        test_path.unlink()
        assert not test_path.exists(), "Failed to remove test file."
    except PermissionError:
        pytest.fail(f"Directory {root / 'data' / 'processed'} is not writable.")
    except Exception as e:
        pytest.fail(f"Unexpected error during write test: {e}")
