"""
Test to verify that data directories (data/raw/ and data/processed/) exist.
This validates task T001d.
"""
import os
import pytest
from pathlib import Path

def test_data_raw_directory_exists():
    """Verify that data/raw/ directory exists."""
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    assert raw_dir.exists(), f"Directory {raw_dir} does not exist"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"

def test_data_processed_directory_exists():
    """Verify that data/processed/ directory exists."""
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    assert processed_dir.exists(), f"Directory {processed_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"

def test_data_gitkeep_files_exist():
    """Verify that .gitkeep files exist in data subdirectories."""
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    assert (raw_dir / ".gitkeep").exists(), f".gitkeep missing in {raw_dir}"
    assert (processed_dir / ".gitkeep").exists(), f".gitkeep missing in {processed_dir}"