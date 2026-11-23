"""
Unit tests for code/define_bbox.py
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, 'code')
from define_bbox import calculate_bounding_box, load_moral_machine_data, save_bounding_box

def test_calculate_bounding_box_basic():
    """Test basic bounding box calculation with expansion."""
    data = {
        'latitude': [10.0, 20.0, 30.0],
        'longitude': [100.0, 110.0, 120.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_bounding_box(df, expand_degrees=2.0)
    
    assert result['min_lat'] == 8.0  # 10 - 2
    assert result['max_lat'] == 32.0  # 30 + 2
    assert result['min_lon'] == 98.0  # 100 - 2
    assert result['max_lon'] == 122.0  # 120 + 2
    assert result['source_records'] == 3
    assert result['expand_degrees'] == 2.0

def test_calculate_bounding_box_with_missing_values():
    """Test that rows with missing lat/lon are excluded."""
    data = {
        'latitude': [10.0, None, 30.0],
        'longitude': [100.0, 110.0, None]
    }
    df = pd.DataFrame(data)
    
    result = calculate_bounding_box(df, expand_degrees=1.0)
    
    # Only first row is valid
    assert result['min_lat'] == 9.0
    assert result['max_lat'] == 11.0
    assert result['min_lon'] == 99.0
    assert result['max_lon'] == 101.0
    assert result['source_records'] == 1

def test_calculate_bounding_box_empty_valid():
    """Test that error is raised when no valid lat/lon exists."""
    data = {
        'latitude': [None, None],
        'longitude': [None, None]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="No valid latitude/longitude data found"):
        calculate_bounding_box(df)

def test_save_bounding_box(tmp_path):
    """Test saving bounding box to JSON."""
    bbox_data = {
        "min_lat": 10.0,
        "max_lat": 20.0,
        "min_lon": 100.0,
        "max_lon": 110.0
    }
    output_file = tmp_path / "test_bbox.json"
    
    save_bounding_box(bbox_data, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == bbox_data

def test_load_moral_machine_data_missing_file():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        load_moral_machine_data("nonexistent_file.csv.gz")

def test_load_moral_machine_data_success(tmp_path):
    """Test loading a valid CSV file."""
    # Create a temporary CSV file
    csv_file = tmp_path / "test_data.csv.gz"
    data = {
        'latitude': [10.0, 20.0],
        'longitude': [100.0, 110.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_file, compression='gzip', index=False)
    
    loaded_df = load_moral_machine_data(csv_file)
    
    assert len(loaded_df) == 2
    assert 'latitude' in loaded_df.columns
    assert 'longitude' in loaded_df.columns