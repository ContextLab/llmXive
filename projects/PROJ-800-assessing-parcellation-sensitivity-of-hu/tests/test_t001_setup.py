"""
Unit tests for T001: Directory Setup.
Verifies that the required directory structure exists after running setup.
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "code",
    "tests",
]

@pytest.fixture(autouse=True)
def ensure_setup():
    """
    Ensures the setup script has been run before tests, or skips if not.
    In a real CI/CD pipeline, this would be handled by the task runner.
    """
    if not PROJECT_ROOT.exists():
        pytest.skip("Project root does not exist. Run setup first.")

def test_project_root_exists():
    """Test that the main project directory exists."""
    assert PROJECT_ROOT.exists(), f"Project root {PROJECT_ROOT} does not exist"
    assert PROJECT_ROOT.is_dir(), f"{PROJECT_ROOT} is not a directory"

def test_required_subdirectories_exist():
    """Test that all required subdirectories exist."""
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_path} (not a directory)")
    
    if missing_dirs:
        pytest.fail(f"Missing or invalid directories: {missing_dirs}")

def test_data_structure():
    """Specific test for the data hierarchy."""
    data_dir = PROJECT_ROOT / "data"
    assert data_dir.exists(), "data/ directory missing"
    
    subdirs = ["raw", "processed", "results"]
    for subdir in subdirs:
        path = data_dir / subdir
        assert path.exists(), f"data/{subdir} missing"
        assert path.is_dir(), f"data/{subdir} is not a directory"
