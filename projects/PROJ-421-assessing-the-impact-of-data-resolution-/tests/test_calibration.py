"""
Unit tests for the calibration module.
"""
import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
import rasterio
from rasterio.transform import from_bounds

# Import the function to test
# Assuming calibration.py is in the code directory and we can import it
# We need to ensure the path is set correctly or use relative imports if in a package
# For this test file, we assume it's run from the project root or code directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from calibration import estimate_lambda, _create_lag_matrix_binary, _log_likelihood_sar


def test_create_lag_matrix_binary():
    """Test the binary weights matrix creation."""
    # Create 4 points in a square
    coords = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ])
    
    # Threshold = 1.5 (should connect diagonals too? No, distance sqrt(2) ~ 1.41 < 1.5)
    # Distance between (0,0) and (1,1) is 1.414.
    W = _create_lag_matrix_binary(coords, threshold=1.5)
    
    # All points should be connected to all others in this small cluster
    # Diagonal should be 0
    assert np.diag(W).sum() == 0.0
    # Row sums should be 1.0 (row standardized)
    assert np.allclose(W.sum(axis=1), 1.0)
    
    # Test with smaller threshold (only orthogonal neighbors)
    W_small = _create_lag_matrix_binary(coords, threshold=1.1)
    # (0,0) connected to (1,0) and (0,1)
    # (0,0) NOT connected to (1,1)
    assert W_small[0, 3] == 0.0 # (0,0) to (1,1)
    assert W_small[0, 1] > 0.0 # (0,0) to (1,0)


def test_log_likelihood_sar():
    """Test the log-likelihood calculation."""
    y = np.array([1.0, 0.0, 1.0, 0.0])
    W = np.eye(4) # Identity (no spatial dependence)
    
    ll = _log_likelihood_sar(y, W, rho=0.0, sigma2=1.0)
    
    # With rho=0, model is y = epsilon ~ N(0, 1)
    # LL = -n/2 log(2pi) - n/2 log(1) - 0.5 * sum(y^2)
    # sum(y^2) = 2
    # LL = -2*log(2pi) - 1
    expected = -0.5 * 4 * np.log(2 * np.pi) - 0.5 * 2
    assert np.isclose(ll, expected)


def test_estimate_lambda_integration(tmp_path):
    """Integration test for estimate_lambda with synthetic data."""
    # Create a synthetic raster in memory
    height, width = 100, 100
    transform = from_bounds(0, 0, 100, 100, width, height)
    
    # Create a pattern with spatial autocorrelation
    data = np.zeros((height, width), dtype=np.uint8)
    # Top half forest, bottom half not (simple block)
    data[:50, :] = 41 # Forest
    data[50:, :] = 11 # Water/Other
    
    # Add some noise
    rng = np.random.default_rng(42)
    noise = rng.choice([0, 1], size=data.shape, p=[0.9, 0.1])
    data = data + noise * 10 # Just to make it distinct if needed, but keeping classes 41 and 11
    
    # Write to temp file
    temp_tif = tmp_path / "test_raster.tif"
    with rasterio.open(
        temp_tif, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=rasterio.uint8,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data, 1)
        
    output_json = tmp_path / "calibration_test.json"
    
    # Run estimation
    result = estimate_lambda(
        input_path=temp_tif,
        output_path=output_json,
        sample_size=500,
        seed=42
    )
    
    # Verify output file exists
    assert output_json.exists()
    
    # Verify JSON content
    with open(output_json, 'r') as f:
        saved_data = json.load(f)
        
    assert "lambda" in saved_data
    assert "seed" in saved_data
    assert saved_data["seed"] == 42
    assert isinstance(saved_data["lambda"], float)
    
    # The lambda should be non-zero if there is spatial structure
    # In our block pattern, there is strong spatial autocorrelation
    # We expect a positive lambda
    assert saved_data["lambda"] > 0.0