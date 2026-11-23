"""
Test to verify the data directory structure created by T001a.
"""
import os
import pytest
from pathlib import Path

def test_data_raw_exists():
    """Verify data/raw directory exists."""
    project_root = Path(__file__).resolve().parent.parent
    data_raw = project_root / "data" / "raw"
    assert data_raw.exists(), f"Directory {data_raw} does not exist"
    assert data_raw.is_dir(), f"{data_raw} is not a directory"

def test_data_processed_exists():
    """Verify data/processed directory exists."""
    project_root = Path(__file__).resolve().parent.parent
    data_processed = project_root / "data" / "processed"
    assert data_processed.exists(), f"Directory {data_processed} does not exist"
    assert data_processed.is_dir(), f"{data_processed} is not a directory"

def test_data_outputs_exists():
    """Verify data/outputs directory exists."""
    project_root = Path(__file__).resolve().parent.parent
    data_outputs = project_root / "data" / "outputs"
    assert data_outputs.exists(), f"Directory {data_outputs} does not exist"
    assert data_outputs.is_dir(), f"{data_outputs} is not a directory"

def test_data_structure_isolation():
    """Verify that the data directory only contains the expected subdirectories."""
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    if not data_root.exists():
        pytest.skip("Data root does not exist yet")

    # List immediate children
    children = [p.name for p in data_root.iterdir() if p.is_dir()]
    expected = {"raw", "processed", "outputs"}
    
    # Ensure no unexpected directories were created at the root of data/
    # (Allowing for potential future additions, but strictly checking the required ones exist)
    assert expected.issubset(set(children)), f"Missing required dirs. Found: {children}, Expected: {expected}"