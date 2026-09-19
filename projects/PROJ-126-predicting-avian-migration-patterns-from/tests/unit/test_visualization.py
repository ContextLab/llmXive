"""
Unit tests for the visualization module.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the functions to test
from visualization import prepare_regional_map_data, generate_regional_map, LAKE_POWELL_BOUNDS

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'grid_id': ['37.0_-111.0', '37.1_-111.2', '36.8_-110.9', '36.0_-110.0'], # Last one is outside bounds
        'week': [10, 10, 10, 10],
        'arrival_date_3': [120.5, 122.0, 118.0, 115.0],
        'arrival_date_5': [121.0, 122.5, 118.5, 115.5],
        'arrival_date_10': [122.0, 123.5, 119.5, 116.5],
        'status': ['determined', 'determined', 'determined', 'undetermined'],
        'lat': [37.0, 37.1, 36.8, 36.0],
        'lon': [-111.0, -111.2, -110.9, -110.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_input_file(sample_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_data.to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

def test_prepare_regional_map_data_filters_region(temp_input_file):
    """Test that prepare_regional_map_data correctly filters for Lake Powell region."""
    result = prepare_regional_map_data(input_file=temp_input_file)
    
    # Check that the row outside bounds is filtered out
    assert len(result) == 3  # Should have 3 rows, excluding the one at lat 36.0
    
    # Check that lat/lon are within bounds
    assert all((result['lat'] >= LAKE_POWELL_BOUNDS['min_lat']) & 
               (result['lat'] <= LAKE_POWELL_BOUNDS['max_lat']))
    assert all((result['lon'] >= LAKE_POWELL_BOUNDS['min_lon']) & 
               (result['lon'] <= LAKE_POWELL_BOUNDS['max_lon']))

def test_prepare_regional_map_data_handles_undetermined(temp_input_file):
    """Test that undetermined status is handled correctly."""
    result = prepare_regional_map_data(input_file=temp_input_file)
    
    # The undetermined row (if it was in bounds) should have NaN
    # In our sample, the undetermined row is out of bounds, so it's filtered.
    # Let's create a case where undetermined is in bounds.
    data = {
        'grid_id': ['37.0_-111.0'],
        'week': [10],
        'arrival_date_3': [120.5],
        'arrival_date_5': [121.0],
        'arrival_date_10': [122.0],
        'status': ['undetermined'],
        'lat': [37.0],
        'lon': [-111.0]
    }
    df_undetermined = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df_undetermined.to_csv(f, index=False)
        temp_file = f.name
    
    try:
        result = prepare_regional_map_data(input_file=temp_file)
        assert pd.isna(result['arrival_date_3'].iloc[0])
        assert pd.isna(result['arrival_date_5'].iloc[0])
        assert pd.isna(result['arrival_date_10'].iloc[0])
    finally:
        os.unlink(temp_file)

def test_generate_regional_map_creates_file(temp_input_file, tmp_path):
    """Test that generate_regional_map creates a valid image file."""
    df = prepare_regional_map_data(input_file=temp_input_file)
    output_path = str(tmp_path / "test_map.png")
    
    generate_regional_map(data=df, output_path=output_path, threshold=5)
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_generate_regional_map_invalid_threshold(temp_input_file, tmp_path):
    """Test that generate_regional_map handles invalid threshold."""
    df = prepare_regional_map_data(input_file=temp_input_file)
    output_path = str(tmp_path / "test_map.png")
    
    # Should raise an error or log a warning if column doesn't exist
    # Our implementation logs an error and returns early
    generate_regional_map(data=df, output_path=output_path, threshold=99)
    
    # File should not be created or be empty if logic returns early
    # In our current implementation, it logs error and returns, so no file.
    # But if the function creates a blank figure, we might need to adjust.
    # For now, assume it doesn't create a file if column is missing.
    # Actually, our code does `return` before saving if column is missing.
    # So the file might not exist.
    # Let's check if the file exists. If the function returns early, it might not.
    # But if we want to be safe, we can check if the file exists.
    # In the current code, if column is missing, it logs error and returns.
    # So the file might not be created.
    # Let's assume the file is not created.
    # However, the function might still create a figure and save it if we don't return.
    # Let's check the code: it does `return` if column is missing.
    # So the file should not be created.
    # But to be safe, we can check.
    if not os.path.exists(output_path):
        pass # Expected
    else:
        # If it exists, it should be empty or invalid?
        # Our code doesn't save if column is missing.
        # So this branch should not be reached.
        assert False, "File should not be created for invalid threshold"

def test_prepare_regional_map_data_missing_file():
    """Test that prepare_regional_map_data raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        prepare_regional_map_data(input_file="non_existent_file.csv")

def test_prepare_regional_map_data_missing_columns(temp_input_file):
    """Test that prepare_regional_map_data raises ValueError for missing columns."""
    # Create a file with missing columns
    data = {
        'grid_id': ['37.0_-111.0'],
        'week': [10],
        # Missing arrival_date_3, etc.
        'status': ['determined'],
        'lat': [37.0],
        'lon': [-111.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_file = f.name
    
    try:
        with pytest.raises(ValueError):
            prepare_regional_map_data(input_file=temp_file)
    finally:
        os.unlink(temp_file)