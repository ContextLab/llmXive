"""
Test to verify the project directory structure exists.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    # Determine the expected root based on standard layout
    # Assuming tests run from repo root
    return Path.cwd() / "projects" / "PROJ-405"

def test_project_root_exists(project_root):
    """Verify the PROJ-405 root directory exists."""
    assert project_root.exists(), f"Project root directory {project_root} does not exist."
    assert project_root.is_dir(), f"{project_root} is not a directory."

def test_required_subdirectories(project_root):
    """Verify all required subdirectories exist."""
    required_dirs = [
        "code",
        "data",
        "tests",
        "artifacts",
        "specs",
        "state",
        "figures"
    ]

    missing = []
    for subdir in required_dirs:
        path = project_root / subdir
        if not path.exists():
            missing.append(subdir)

    assert len(missing) == 0, f"Missing required subdirectories: {missing}"

def test_specs_contracts_exists(project_root):
    """Verify the specific specs/contracts path exists."""
    path = project_root / "specs" / "001-predict-plant-disease-severity" / "contracts"
    assert path.exists(), f"Contracts directory missing: {path}"
    assert path.is_dir(), f"{path} is not a directory."