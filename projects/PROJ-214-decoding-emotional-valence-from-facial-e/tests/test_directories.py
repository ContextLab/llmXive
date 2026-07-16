"""
Tests to verify the project directory structure exists as expected.
"""
import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory (parent of 'code' and 'tests')."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent


def test_data_raw_exists(project_root):
    """Verify that data/raw directory exists."""
    data_raw = project_root / "data" / "raw"
    assert data_raw.exists(), f"Directory {data_raw} does not exist"
    assert data_raw.is_dir(), f"{data_raw} is not a directory"


def test_data_processed_exists(project_root):
    """Verify that data/processed directory exists."""
    data_processed = project_root / "data" / "processed"
    assert data_processed.exists(), f"Directory {data_processed} does not exist"
    assert data_processed.is_dir(), f"{data_processed} is not a directory"


def test_data_models_exists(project_root):
    """Verify that data/models directory exists."""
    data_models = project_root / "data" / "models"
    assert data_models.exists(), f"Directory {data_models} does not exist"
    assert data_models.is_dir(), f"{data_models} is not a directory"


def test_directory_structure_complete(project_root):
    """Verify the complete expected directory structure."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/models",
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)

    assert not missing, f"Missing directories: {missing}"