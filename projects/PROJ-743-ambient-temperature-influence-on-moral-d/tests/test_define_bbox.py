"""
Tests for define_bbox.py
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Import the module functions
from code.define_bbox import calculate_bounding_box, save_bounding_box, load_moral_machine_data

def test_calculate_bounding_box_basic():
    """Test basic bounding box calculation."""
    data = {
        'latitude': [10.0, 20.0, 30.0],
        'longitude': [5.0, 15.0, 25.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_bounding_box(df, expand_degrees=1.0)
    
    assert result['min_lat'] == 9.0
    assert result['max_lat'] == 31.0
    assert result['min_lon'] == 4.0
    assert result['max_lon'] == 26.0
    assert result['source_records'] == 3

def test_calculate_bounding_box_with_nulls():
    """Test bounding box calculation ignores null values."""
    data = {
        'latitude': [10.0, None, 30.0],
        'longitude': [5.0, 15.0, None]
    }
    df = pd.DataFrame(data)
    
    # Only the first row is valid
    result = calculate_bounding_box(df, expand_degrees=0.0)
    
    assert result['min_lat'] == 10.0
    assert result['max_lat'] == 10.0
    assert result['min_lon'] == 5.0
    assert result['max_lon'] == 5.0
    assert result['source_records'] == 1

def test_save_and_load_bounding_box():
    """Test saving and loading bounding box to JSON."""
    bbox_data = {
        "min_lat": 10.0,
        "max_lat": 20.0,
        "min_lon": 5.0,
        "max_lon": 15.0
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "bbox.json"
        save_bounding_box(bbox_data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == bbox_data

def test_load_moral_machine_data_missing_file():
    """Test that load_moral_machine_data raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_moral_machine_data("non_existent_file.csv.gz")