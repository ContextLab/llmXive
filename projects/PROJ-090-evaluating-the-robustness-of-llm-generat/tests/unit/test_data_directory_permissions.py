"""
Integration test to verify data directory permissions after setup.

This test is designed to be run after the setup script has been executed.
It verifies that the directories exist and have the correct permissions.
"""
import os
import stat
from pathlib import Path
import pytest

REQUIRED_DIRS = [
    "data",
    "data/raw",
    "data/processed",
    "data/logs"
]

EXPECTED_PERMISSIONS = 0o755


@pytest.fixture(scope="module")
def project_root():
    """Get the project root directory."""
    # Assume tests are in tests/unit/, project root is two levels up
    return Path(__file__).parent.parent.parent


def test_data_directories_exist(project_root):
    """Verify that all required data directories exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
        elif not full_path.is_dir():
            missing.append(f"{dir_path} (not a directory)")
    
    if missing:
        pytest.fail(f"The following directories are missing or invalid: {missing}")

def test_data_directory_permissions(project_root):
    """Verify that all data directories have 755 permissions."""
    permission_errors = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            # Already checked in other test, skip
            continue
            
        mode = os.stat(full_path).st_mode & 0o777
        if mode != EXPECTED_PERMISSIONS:
            permission_errors.append(
                f"{dir_path}: expected {oct(EXPECTED_PERMISSIONS)}, got {oct(mode)}"
            )
    
    if permission_errors:
        pytest.fail("Permission errors found:\n" + "\n".join(permission_errors))

def test_data_directory_structure(project_root):
    """Verify the overall structure of the data directory."""
    data_dir = project_root / "data"
    
    # Check base data dir
    assert data_dir.exists(), "data/ directory does not exist"
    assert data_dir.is_dir(), "data/ is not a directory"
    
    # Check subdirectories
    expected_subdirs = ["raw", "processed", "logs"]
    for subdir in expected_subdirs:
        subdir_path = data_dir / subdir
        assert subdir_path.exists(), f"data/{subdir}/ does not exist"
        assert subdir_path.is_dir(), f"data/{subdir}/ is not a directory"