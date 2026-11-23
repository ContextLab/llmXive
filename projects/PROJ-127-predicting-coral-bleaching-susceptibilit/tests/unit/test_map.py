"""
Unit tests for map.py functions.
"""
import os
import json
import tempfile
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import rasterio
from rasterio.transform import from_origin
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Import functions to test
# Note: In a real scenario, we would import from code.map
# For this test, we assume the functions are available
# from code.map import load_raster, generate_risk_map, identify_dominant_drivers, threshold_sensitivity, validate_map_against_independent_reports


def create_temp_raster(path, data, transform, crs):
    """Helper to create a temporary GeoTIFF file."""
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1,
        'width': data.shape[1],
        'height': data.shape[0],
        'transform': transform,
        'crs': crs,
        'nodata': -9999
    }
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)


@pytest.fixture
def temp_rasters():
    """Create temporary rasters for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sst_path = os.path.join(tmpdir, 'sst.tif')
        dhw_path = os.path.join(tmpdir, 'dhw.tif')
        
        # Create dummy data
        data = np.random.rand(10, 10).astype(np.float32) * 10 + 20
        transform = from_origin(0, 10, 1, 1)
        crs = 'EPSG:4326'
        
        create_temp_raster(sst_path, data, transform, crs)
        create_temp_raster(dhw_path, data, transform, crs)
        
        yield sst_path, dhw_path, tmpdir


@pytest.fixture
def temp_model_and_scaler():
    """Create temporary model and scaler files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'model.pkl')
        scaler_path = os.path.join(tmpdir, 'scaler.pkl')
        
        # Create dummy model and scaler
        model = RandomForestClassifier(n_estimators=2)
        scaler = StandardScaler()
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        yield model_path, scaler_path, tmpdir


def test_load_raster(temp_rasters):
    """Test loading a raster file."""
    sst_path, _, _ = temp_rasters
    data, meta = load_raster(sst_path)
    
    assert data.shape == (10, 10)
    assert meta['dtype'] == 'float32'
    assert 'transform' in meta
    assert 'crs' in meta


def test_generate_risk_map(temp_rasters, temp_model_and_scaler):
    """Test generating a risk map."""
    sst_path, dhw_path, tmpdir = temp_rasters
    model_path, scaler_path, _ = temp_model_and_scaler
    output_path = os.path.join(tmpdir, 'risk_map.tif')
    
    generate_risk_map(sst_path, dhw_path, model_path, scaler_path, output_path)
    
    assert os.path.exists(output_path)
    
    # Verify output
    risk_data, risk_meta = load_raster(output_path)
    assert risk_data.shape == (10, 10)
    assert risk_data.dtype == np.float32
    
    # Check values are in [0, 1]
    valid_values = risk_data[~np.isnan(risk_data)]
    assert np.all(valid_values >= 0.0)
    assert np.all(valid_values <= 1.0)


def test_threshold_sensitivity(temp_rasters):
    """Test threshold sensitivity analysis."""
    sst_path, dhw_path, tmpdir = temp_rasters
    # Create a dummy risk map
    risk_path = os.path.join(tmpdir, 'risk_map.tif')
    risk_data = np.random.rand(10, 10).astype(np.float32)
    transform = from_origin(0, 10, 1, 1)
    crs = 'EPSG:4326'
    create_temp_raster(risk_path, risk_data, transform, crs)
    
    thresholds = [0.3, 0.5, 0.7]
    results = threshold_sensitivity(risk_path, thresholds)
    
    assert len(results) == 3
    for thresh in thresholds:
        assert str(thresh) in results
        assert 'pixels_above' in results[str(thresh)]
        assert 'pixels_below' in results[str(thresh)]
        assert 'fraction_above' in results[str(thresh)]


def test_validate_map_against_independent_reports(temp_rasters):
    """Test validation against independent reports."""
    sst_path, dhw_path, tmpdir = temp_rasters
    risk_path = os.path.join(tmpdir, 'risk_map.tif')
    risk_data = np.random.rand(10, 10).astype(np.float32)
    transform = from_origin(0, 10, 1, 1)
    crs = 'EPSG:4326'
    create_temp_raster(risk_path, risk_data, transform, crs)
    
    # Test without independent data
    result = validate_map_against_independent_reports(risk_path)
    assert result['independent_data_available'] is False
    
    # Test with non-existent file
    result = validate_map_against_independent_reports(risk_path, 'non_existent.csv')
    assert result['independent_data_available'] is False
    
    # Test with existing file (dummy)
    events_path = os.path.join(tmpdir, 'events.csv')
    pd.DataFrame({'reef_id': [1, 2], 'bleaching': [1, 0]}).to_csv(events_path, index=False)
    result = validate_map_against_independent_reports(risk_path, events_path)
    assert result['independent_data_available'] is True