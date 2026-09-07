"""
Test to verify that required data directories exist and contain .gitkeep files.
This ensures T008 is satisfied.
"""
import os
from pathlib import Path

def test_data_raw_directory_exists():
    """Verify data/raw/ directory exists."""
    raw_dir = Path("data/raw")
    assert raw_dir.exists(), f"Directory {raw_dir} does not exist"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"

def test_data_processed_directory_exists():
    """Verify data/processed/ directory exists."""
    processed_dir = Path("data/processed")
    assert processed_dir.exists(), f"Directory {processed_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"

def test_gitkeep_in_raw():
    """Verify .gitkeep exists in data/raw/."""
    gitkeep = Path("data/raw/.gitkeep")
    assert gitkeep.exists(), f"File {gitkeep} does not exist"
    assert gitkeep.is_file(), f"{gitkeep} is not a file"

def test_gitkeep_in_processed():
    """Verify .gitkeep exists in data/processed/."""
    gitkeep = Path("data/processed/.gitkeep")
    assert gitkeep.exists(), f"File {gitkeep} does not exist"
    assert gitkeep.is_file(), f"{gitkeep} is not a file"