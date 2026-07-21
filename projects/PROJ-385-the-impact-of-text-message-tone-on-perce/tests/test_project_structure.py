"""
Test suite to verify that the project structure (T001) has been correctly initialized.
This test ensures that all required directories exist as per the implementation plan.
"""
import os
import pytest
from pathlib import Path

# Import the config to get the project root
# We assume this file is run from the project root or code/ directory context
# Adjust import if necessary based on PYTHONPATH
try:
    from config import get_project_root
except ImportError:
    # Fallback for running tests directly without package installation
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from config import get_project_root


REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/consent",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "specs",
    "specs/001-text-tone-emotional-support",
    "specs/001-text-tone-emotional-support/contracts",
    "figures"
]


def test_project_root_exists():
    """Verify that the project root can be determined."""
    root = get_project_root()
    assert root.exists(), f"Project root path {root} does not exist."
    assert root.is_dir(), f"Project root path {root} is not a directory."


@pytest.mark.parametrize("relative_dir", REQUIRED_DIRS)
def test_required_directory_exists(relative_dir):
    """
    Verify that each required directory specified in T001 exists.
    """
    root = get_project_root()
    full_path = root / relative_dir
    
    assert full_path.exists(), f"Required directory missing: {full_path}"
    assert full_path.is_dir(), f"Required path is not a directory: {full_path}"


def test_data_subdirectory_structure():
    """
    Specific check for the data directory hierarchy to ensure subdirectories are present.
    """
    root = get_project_root()
    data_dir = root / "data"
    
    assert data_dir.exists(), "Data directory missing."
    
    # Check specific subdirectories required for data handling
    subdirs = ["raw", "processed", "consent"]
    for subdir in subdirs:
        path = data_dir / subdir
        assert path.exists(), f"Missing data subdirectory: {path}"
        assert path.is_dir(), f"Data subdirectory is not a directory: {path}"
