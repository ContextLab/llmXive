import os
import pytest
from pathlib import Path

@pytest.mark.parametrize("dir_name", [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "docs"
])
def test_required_directories_exist(dir_name):
    """
    Verify that the required project directories exist after setup.
    """
    base_path = Path(".")
    target_path = base_path / dir_name
    
    assert target_path.exists(), f"Directory {dir_name} does not exist"
    assert target_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_data_raw_subdirectory():
    """
    Specifically check data/raw exists as a subdirectory of data.
    """
    data_raw = Path("data/raw")
    assert data_raw.exists() and data_raw.is_dir()

def test_data_processed_subdirectory():
    """
    Specifically check data/processed exists as a subdirectory of data.
    """
    data_processed = Path("data/processed")
    assert data_processed.exists() and data_processed.is_dir()