import os
import pytest
from pathlib import Path
from setup_directories import setup_directories

def test_setup_directories_creates_required_folders():
    """
    Test that setup_directories creates the required directory structure:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    """
    # Run the setup function
    result = setup_directories()

    # Assert the function returned True
    assert result is True

    # Check that each required directory exists
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests"
    ]

    for dir_path in required_dirs:
        full_path = Path(dir_path)
        assert full_path.exists(), f"Directory {dir_path} was not created"
        assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_data_raw_directory_exists():
    """
    Specific test for T001b: Verify data/raw/ directory exists.
    """
    # Ensure directories are set up
    setup_directories()

    # Check specifically for data/raw
    data_raw_path = Path("data/raw")
    assert data_raw_path.exists(), "data/raw directory does not exist"
    assert data_raw_path.is_dir(), "data/raw exists but is not a directory"