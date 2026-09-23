import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.setup_data_structure import setup_directories, get_project_root


@pytest.fixture
def temp_root():
    """Create a temporary directory to act as project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_required_directories_exist(temp_root):
    """Verify that setup_directories creates the required data structure."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/processed/results",
        "state",
        "docs",
        "code",
        "code/src",
        "code/src/ingestion",
        "code/src/preprocessing",
        "code/src/analysis",
        "code/src/utils",
        "code/tests",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
    ]

    # Run the setup function
    setup_directories(temp_root)

    # Verify each directory exists
    for dir_path in required_dirs:
        full_path = Path(temp_root) / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created"
        assert full_path.is_dir(), f"Path {dir_path} is not a directory"


def test_test_directories_exist(temp_root):
    """Specifically verify test directory structure."""
    setup_directories(temp_root)

    test_dirs = [
        "code/tests",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
    ]

    for dir_path in test_dirs:
        full_path = Path(temp_root) / dir_path
        assert full_path.exists() and full_path.is_dir(), \
            f"Test directory {dir_path} missing"
