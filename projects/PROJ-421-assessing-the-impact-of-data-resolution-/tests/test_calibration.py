"""
Tests for the calibration module (T010).
"""
import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Mock the config and utils if necessary, but ideally run against real structure
# We will test the logic of estimate_lambda with a synthetic but structured input
# that mimics the spatial autocorrelation expected in real data.

def test_estimate_lambda_logic():
    """
    Test that estimate_lambda runs without error on a synthetic dataset
    that has known spatial structure.
    """
    # This test requires the actual calibration module to be importable.
    # We will create a temporary GeoTIFF with synthetic data to test the pipeline.
    
    try:
        import rasterio
        from rasterio.transform import from_bounds
    except ImportError:
        pytest.skip("rasterio not installed for testing")

    from calibration import estimate_lambda

    # Create a synthetic raster with spatial autocorrelation
    # Use a simple autoregressive process: y_t = lambda * y_neighbors + error
    n = 50
    data = np.random.rand(n, n)
    
    # Inject spatial autocorrelation manually (smoothing)
    # This is a crude approximation but sufficient to trigger the MLE
    # We'll use a simple convolution to create smooth regions
    kernel = np.array([[0.1, 0.2, 0.1],
                       [0.2, 0.2, 0.2],
                       [0.1, 0.2, 0.1]])
    from scipy.signal import convolve2d
    data = convolve2d(data, kernel, mode='same')
    
    # Add some noise
    data += np.random.normal(0, 0.1, data.shape)
    
    # Create a temporary GeoTIFF
    with tempfile.TemporaryDirectory() as tmpdir:
        tiff_path = os.path.join(tmpdir, "test_30m.tif")
        transform = from_bounds(0, 0, 1, 1, n, n)
        
        with rasterio.open(
            tiff_path, 'w',
            driver='GTiff',
            height=n,
            width=n,
            count=1,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(data, 1)
        
        # Run the estimation
        lambda_val = estimate_lambda(tiff_path)
        
        assert isinstance(lambda_val, float), "Lambda must be a float"
        assert not np.isnan(lambda_val), "Lambda must not be NaN"
        assert not np.isinf(lambda_val), "Lambda must not be Inf"
        # Lambda for spatial lag is typically between -1 and 1
        assert -1 < lambda_val < 1, f"Lambda {lambda_val} is out of expected range [-1, 1]"

def test_save_calibration_result():
    """
    Test that save_calibration_result writes a valid JSON file.
    """
    from calibration import save_calibration_result
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "calibration_lambda.json")
        save_calibration_result(0.5, output_path)
        
        assert os.path.exists(output_path), "Output file must exist"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "lambda" in data
        assert data["lambda"] == 0.5
        assert "seed" in data
        assert "method" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])