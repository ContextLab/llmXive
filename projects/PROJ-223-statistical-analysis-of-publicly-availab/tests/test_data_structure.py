"""
Tests for the data directory structure creation (T001c).
Verifies that data/raw/, data/processed/, and data/reports/ exist.
"""
import os
import pytest
from pathlib import Path
from config import PROJECT_ROOT

@pytest.fixture(scope="module")
def data_root():
    return Path(PROJECT_ROOT) / "data"

def test_data_directory_exists(data_root):
    """Test that the main data directory exists."""
    assert data_root.exists(), f"Data directory {data_root} does not exist"
    assert data_root.is_dir(), f"{data_root} is not a directory"

def test_raw_directory_exists(data_root):
    """Test that data/raw/ exists."""
    raw_dir = data_root / "raw"
    assert raw_dir.exists(), f"Raw data directory {raw_dir} does not exist"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"

def test_processed_directory_exists(data_root):
    """Test that data/processed/ exists."""
    processed_dir = data_root / "processed"
    assert processed_dir.exists(), f"Processed data directory {processed_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"

def test_reports_directory_exists(data_root):
    """Test that data/reports/ exists."""
    reports_dir = data_root / "reports"
    assert reports_dir.exists(), f"Reports directory {reports_dir} does not exist"
    assert reports_dir.is_dir(), f"{reports_dir} is not a directory"

def test_all_required_subdirectories_exist(data_root):
    """Test that all required subdirectories exist."""
    required_dirs = ["raw", "processed", "reports"]
    for subdir in required_dirs:
        dir_path = data_root / subdir
        assert dir_path.exists(), f"Required directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"