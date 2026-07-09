"""
Unit tests to verify the data directory structure exists as required by T005.
"""
import os
import pytest
from pathlib import Path

def test_data_directory_exists():
    """Verify the main data directory exists."""
    # Assuming tests are run from project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    assert data_dir.exists(), "data/ directory must exist"
    assert data_dir.is_dir(), "data/ must be a directory"

def test_raw_subdirectory_exists():
    """Verify the raw/ subdirectory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    assert raw_dir.exists(), "data/raw/ directory must exist"
    assert raw_dir.is_dir(), "data/raw/ must be a directory"

def test_processed_subdirectory_exists():
    """Verify the processed/ subdirectory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    processed_dir = project_root / "data" / "processed"
    assert processed_dir.exists(), "data/processed/ directory must exist"
    assert processed_dir.is_dir(), "data/processed/ must be a directory"

def test_contracts_subdirectory_exists():
    """Verify the contracts/ subdirectory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    contracts_dir = project_root / "data" / "contracts"
    assert contracts_dir.exists(), "data/contracts/ directory must exist"
    assert contracts_dir.is_dir(), "data/contracts/ must be a directory"

def test_readme_exists():
    """Verify data/README.md exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    readme = project_root / "data" / "README.md"
    assert readme.exists(), "data/README.md must exist"
    assert readme.is_file(), "data/README.md must be a file"