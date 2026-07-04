"""
Unit test to verify that T001b subdirectories were created correctly.
This test ensures the directory structure matches the requirement.
"""
import os
import pytest
from pathlib import Path

# Define the project root path
PROJECT_ID = "PROJ-160-investigating-the-impact-of-early-life-s"
BASE_DIR = Path("projects") / PROJECT_ID

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "tests",
    "contracts"
]

@pytest.fixture(scope="module")
def project_path():
    """Return the base project path."""
    return BASE_DIR

def test_project_root_exists(project_path):
    """Verify the base project directory exists."""
    assert project_path.exists(), f"Base project directory {project_path} does not exist."
    assert project_path.is_dir(), f"{project_path} is not a directory."

def test_required_subdirectories_exist(project_path):
    """Verify all required subdirectories exist and are directories."""
    for dir_name in REQUIRED_DIRS:
        dir_path = project_path / dir_name
        assert dir_path.exists(), f"Required directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory."

def test_data_raw_is_subdirectory_of_data(project_path):
    """Verify data/raw is correctly nested under data."""
    data_path = project_path / "data"
    raw_path = project_path / "data" / "raw"
    processed_path = project_path / "data" / "processed"
    
    assert data_path.exists(), "Parent 'data' directory missing."
    assert raw_path.exists(), "Subdirectory 'data/raw' missing."
    assert processed_path.exists(), "Subdirectory 'data/processed' missing."
    
    # Verify they are actually inside the data directory
    assert raw_path.parent == data_path, "data/raw is not inside data/"
    assert processed_path.parent == data_path, "data/processed is not inside data/"