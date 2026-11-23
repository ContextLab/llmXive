"""
Unit tests for the derive_bbox module.
"""
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project_root))

from derive_bbox import calculate_bounding_box, save_bounding_box, load_moral_machine_data

def test_calculate_bounding_box_basic():
    """Test bounding box calculation with simple data."""
    data = {
        'latitude': [10.0, 20.0, 30.0],
        'longitude': [-5.0, 0.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    bbox = calculate_bounding_box(df)
    
    assert bbox['min_lat'] == 10.0
    assert bbox['max_lat'] == 30.0
    assert bbox['min_lon'] == -5.0
    assert bbox['max_lon'] == 5.0

def test_calculate_bounding_box_with_nan():
    """Test that NaN values are handled correctly."""
    data = {
        'latitude': [10.0, None, 30.0],
        'longitude': [-5.0, 0.0, None]
    }
    df = pd.DataFrame(data)
    
    # Should not raise and should calculate based on valid rows
    bbox = calculate_bounding_box(df)
    
    assert bbox['min_lat'] == 10.0
    assert bbox['max_lat'] == 30.0
    assert bbox['min_lon'] == -5.0
    assert bbox['max_lon'] == 0.0

def test_calculate_bounding_box_empty_after_dropna():
    """Test that ValueError is raised when no valid coordinates exist."""
    data = {
        'latitude': [None, None],
        'longitude': [None, None]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="No valid latitude/longitude coordinates found"):
        calculate_bounding_box(df)

def test_save_and_load_bounding_box(tmp_path):
    """Test saving and loading bounding box to/from JSON."""
    bbox = {
        "min_lat": -10.5,
        "max_lat": 45.2,
        "min_lon": -180.0,
        "max_lon": 179.9
    }
    
    output_file = tmp_path / "test_bbox.json"
    save_bounding_box(bbox, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded_bbox = json.load(f)
    
    assert loaded_bbox == bbox

def test_load_moral_machine_data_missing_file():
    """Test that FileNotFoundError is raised when dataset is missing."""
    # Ensure the path doesn't exist
    fake_path = Path("/tmp/nonexistent_moral_machine_data.csv.gz")
    
    # Temporarily override the environment variable to point to non-existent file
    old_env = os.environ.get("MORAL_MACHINE_DATA_PATH")
    try:
        os.environ["MORAL_MACHINE_DATA_PATH"] = str(fake_path)
        with pytest.raises(FileNotFoundError):
            load_moral_machine_data()
    finally:
        if old_env:
            os.environ["MORAL_MACHINE_DATA_PATH"] = old_env
        elif "MORAL_MACHINE_DATA_PATH" in os.environ:
            del os.environ["MORAL_MACHINE_DATA_PATH"]