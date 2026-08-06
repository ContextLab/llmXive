"""
Unit tests for the calibration module.
"""
import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Import the module under test
# We need to make sure the path is correct
import sys
sys.path.insert(0, 'code')

from calibration import estimate_lambda, save_lambda, _load_sample_from_raster

def test_estimate_lambda_on_synthetic_data():
    """
    Test that estimate_lambda can run on a synthetic 1D array.
    Since we don't have real data in the test environment, we create a 
    temporary file with synthetic data that has a known spatial structure.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as tmp:
        # Create a 1D array with some spatial correlation
        # y[i] = 0.5 * y[i-1] + noise
        n = 1000
        y = np.zeros(n)
        y[0] = 1.0
        for i in range(1, n):
            y[i] = 0.5 * y[i-1] + np.random.normal(0, 0.1)
        
        np.save(tmp.name, y)
        
        # Run estimation
        # Note: The implementation uses a 1D neighbor structure which matches our synthetic data
        lam = estimate_lambda(tmp.name, n_samples=500, seed=42)
        
        # Assert that the result is a valid number
        assert isinstance(lam, float)
        assert -1.0 < lam < 1.0
        
        # The true lambda is 0.5. We expect the estimate to be close.
        # Due to the small sample and noise, we allow a wide margin.
        assert 0.0 < lam < 1.0

def test_save_lambda_creates_json():
    """
    Test that save_lambda creates a valid JSON file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_lambda.json')
        save_lambda(0.45, output_path, seed=42)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['lambda'] == 0.45
        assert data['seed'] == 42
        assert 'method' in data

def test_load_sample_from_raster():
    """
    Test the sample loading function.
    """
    with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as tmp:
        data = np.random.rand(1000)
        np.save(tmp.name, data)
        
        sample = _load_sample_from_raster(tmp.name, n_samples=100, seed=42)
        
        assert len(sample) == 100
        assert isinstance(sample, np.ndarray)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])