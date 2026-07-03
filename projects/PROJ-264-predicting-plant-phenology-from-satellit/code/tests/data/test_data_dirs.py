import os
from pathlib import Path
import pytest

def test_raw_directory_exists():
    """Verify that the data/raw directory exists."""
    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw"
    assert raw_dir.exists(), f"Directory {raw_dir} does not exist."
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory."

def test_processed_directory_exists():
    """Verify that the data/processed directory exists."""
    root = Path(__file__).resolve().parents[2]
    processed_dir = root / "data" / "processed"
    assert processed_dir.exists(), f"Directory {processed_dir} does not exist."
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory."

def test_gitkeep_exists_in_raw():
    """Verify that .gitkeep exists in data/raw to ensure directory persistence."""
    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw"
    gitkeep = raw_dir / ".gitkeep"
    assert gitkeep.exists(), f".gitkeep missing in {raw_dir}"

def test_gitkeep_exists_in_processed():
    """Verify that .gitkeep exists in data/processed to ensure directory persistence."""
    root = Path(__file__).resolve().parents[2]
    processed_dir = root / "data" / "processed"
    gitkeep = processed_dir / ".gitkeep"
    assert gitkeep.exists(), f".gitkeep missing in {processed_dir}"