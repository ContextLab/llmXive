"""
Integration test to verify the project directory structure is correctly created.
This test ensures that T001 has successfully set up the required folders.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Determine the project root directory."""
    current = Path.cwd()
    if (current / "code").exists():
        return current
    parent = current.parent
    if (parent / "code").exists() and current.name == "code":
        return parent
    return current

def test_required_directories_exist(project_root):
    """Assert that all required directories from T001 exist."""
    required_dirs = [
        "code/src",
        "code/src/utils",
        "code/src/ingestion",
        "code/src/preprocessing",
        "code/src/features",
        "code/src/models",
        "code/src/validation",
        "code/tests/unit",
        "code/tests/integration",
        "data/raw",
        "data/processed",
        "data/figures",
        "docs/reports",
        "specs/001-predict-heusler-hysteresis",
        "specs/001-predict-heusler-hysteresis/contracts",
        "state/projects",
        "logs",
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)

    assert not missing, f"The following required directories are missing: {missing}"

def test_gitkeep_files_exist(project_root):
    """Assert that .gitkeep files exist in data directories to preserve them in git."""
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/figures",
        "code/src",
        "code/tests/unit",
        "code/tests/integration",
    ]

    for dir_path in data_dirs:
        full_path = project_root / dir_path
        gitkeep = full_path / ".gitkeep"
        # Only assert if the directory is expected to be tracked (data folders specifically)
        # In some workflows, .gitkeep might not be strictly required for src, but good practice.
        if dir_path.startswith("data"):
            assert gitkeep.exists(), f".gitkeep missing in {full_path}"