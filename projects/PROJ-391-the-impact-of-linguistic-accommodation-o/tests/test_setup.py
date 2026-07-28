"""
Tests for the project setup script (T001a).

Verifies that the required directory structure exists after running setup_directories.py.
"""
import os
import pytest
import subprocess
import sys

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "tests",
    "outputs",
    "outputs/figures",
    "outputs/reports"
]

def ensure_setup_ran():
    """Run the setup script if directories don't exist."""
    missing = [d for d in REQUIRED_DIRS if not os.path.isdir(d)]
    if missing:
        # Run the setup script
        result = subprocess.run(
            [sys.executable, "code/setup_directories.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.fail(f"Setup script failed: {result.stderr}")

@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """Ensure the environment is set up before running tests."""
    ensure_setup_ran()
    yield

def test_required_directories_exist():
    """Verify all required directories exist."""
    missing = [d for d in REQUIRED_DIRS if not os.path.isdir(d)]
    assert not missing, f"The following directories are missing: {missing}"

def test_data_raw_is_directory():
    """Verify data/raw is a directory."""
    assert os.path.isdir("data/raw"), "data/raw is not a directory"

def test_data_processed_is_directory():
    """Verify data/processed is a directory."""
    assert os.path.isdir("data/processed"), "data/processed is not a directory"

def test_outputs_figures_is_directory():
    """Verify outputs/figures is a directory."""
    assert os.path.isdir("outputs/figures"), "outputs/figures is not a directory"

def test_outputs_reports_is_directory():
    """Verify outputs/reports is a directory."""
    assert os.path.isdir("outputs/reports"), "outputs/reports is not a directory"