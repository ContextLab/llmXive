"""
Unit tests to verify that the project directory structure is correctly initialized.
"""
import os
import pytest
from pathlib import Path

# Define the expected directory structure relative to the project root
EXPECTED_DIRS = [
    "data/raw",
    "data/processed",
    "data/assets",
    "code",
    "artifacts",
    "artifacts/logs",
    "artifacts/weights",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

@pytest.fixture
def project_root():
    """Get the project root directory (parent of the tests directory)."""
    return Path(__file__).parent.parent.parent

def test_directories_exist(project_root):
    """Verify that all required directories exist."""
    for dir_path in EXPECTED_DIRS:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"

def test_data_assets_has_gitkeep(project_root):
    """Verify that data/assets contains a .gitkeep file to ensure tracking."""
    gitkeep_path = project_root / "data/assets/.gitkeep"
    assert gitkeep_path.exists(), f".gitkeep file missing in data/assets: {gitkeep_path}"